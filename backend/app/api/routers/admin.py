"""Administration API (consumed by the React admin dashboard)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import admin_user
from app.db import get_session
from app.models import (
    AuditLog,
    Booking,
    BookingStatus,
    Category,
    Plan,
    Professional,
    ProStatus,
    Report,
    ReportStatus,
    Review,
    ReviewStatus,
    User,
    WorkMode,
)
from app.schemas.common import BookingOut, CategoryIn, CategoryOut, ReviewOut, UserOut
from app.services import admin as admin_service
from app.services import reviews as review_service
from app.services.audit import audit

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(admin_user)])


def page(items, total: int) -> dict:
    return {"items": items, "total": total}


@router.get("/stats")
async def stats(days: int = Query(30, ge=1, le=365), session: AsyncSession = Depends(get_session)):
    return await admin_service.platform_stats(session, days)


# --- Users -----------------------------------------------------------------------
@router.get("/users")
async def users(q: str | None = None, limit: int = Query(50, le=200), offset: int = 0,
                session: AsyncSession = Depends(get_session)):
    stmt = select(User).where(User.deleted_at.is_(None))
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(User.username).like(like), func.lower(User.first_name).like(like),
                              func.lower(User.last_name).like(like), func.lower(User.email).like(like)))
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = (await session.execute(stmt.order_by(User.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    return page([UserOut.model_validate(u) for u in rows], total)


@router.post("/users/{user_id}/ban")
async def ban(user_id: int, banned: bool = True, admin: User = Depends(admin_user),
              session: AsyncSession = Depends(get_session)):
    try:
        u = await admin_service.set_user_banned(session, admin, user_id, banned)
    except admin_service.AdminError as exc:
        raise HTTPException(422, str(exc)) from exc
    return UserOut.model_validate(u)


# --- Professionals -----------------------------------------------------------------
@router.get("/professionals")
async def professionals(status: str | None = None, q: str | None = None, limit: int = Query(50, le=200),
                        offset: int = 0, session: AsyncSession = Depends(get_session)):
    stmt = select(Professional).options(selectinload(Professional.category))
    if status:
        stmt = stmt.where(Professional.status == ProStatus(status))
    if q:
        stmt = stmt.where(func.lower(Professional.business_name).like(f"%{q.lower()}%"))
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = (await session.execute(stmt.order_by(Professional.created_at.desc()).limit(limit).offset(offset))
            ).scalars().all()
    return page([{
        "id": p.id, "business_name": p.business_name, "category": p.category.name("fr"), "city": p.city,
        "work_mode": p.work_mode.value, "status": p.status.value, "is_verified": p.is_verified,
        "rating_avg": p.rating_avg, "rating_count": p.rating_count, "completed_count": p.completed_count,
        "created_at": p.created_at, "phone": p.phone, "description": p.description,
    } for p in rows], total)


class ProStatusIn(BaseModel):
    status: str
    verify: bool | None = None


@router.post("/professionals/{pro_id}/status")
async def set_pro_status(pro_id: int, body: ProStatusIn, admin: User = Depends(admin_user),
                         session: AsyncSession = Depends(get_session)):
    try:
        pro = await admin_service.set_pro_status(session, admin, pro_id, ProStatus(body.status), body.verify)
    except (admin_service.AdminError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"id": pro.id, "status": pro.status.value, "is_verified": pro.is_verified}


# --- Categories -------------------------------------------------------------------
@router.get("/categories", response_model=list[CategoryOut])
async def categories(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(Category).order_by(Category.parent_id.nulls_first(), Category.sort_order))
            ).scalars().all()
    return [CategoryOut.model_validate({**{k: getattr(c, k) for k in CategoryOut.model_fields if k != "children"},
                                        "children": []}) for c in rows]


@router.post("/categories", response_model=CategoryOut, status_code=201)
async def create_category(body: CategoryIn, admin: User = Depends(admin_user),
                          session: AsyncSession = Depends(get_session)):
    if (await session.execute(select(Category.id).where(Category.slug == body.slug))).first():
        raise HTTPException(409, "Slug already exists")
    data = body.model_dump()
    data["default_work_mode"] = WorkMode(data["default_work_mode"])
    cat = Category(**data)
    session.add(cat)
    await session.flush()
    audit(session, "category.create", "category", cat.id, admin.id, slug=cat.slug)
    await session.commit()
    return CategoryOut.model_validate({**{k: getattr(cat, k) for k in CategoryOut.model_fields if k != "children"},
                                       "children": []})


@router.put("/categories/{cat_id}", response_model=CategoryOut)
async def update_category(cat_id: int, body: CategoryIn, admin: User = Depends(admin_user),
                          session: AsyncSession = Depends(get_session)):
    cat = await session.get(Category, cat_id)
    if cat is None:
        raise HTTPException(404, "Unknown category")
    data = body.model_dump()
    data["default_work_mode"] = WorkMode(data["default_work_mode"])
    if data["parent_id"] == cat.id:
        raise HTTPException(422, "A category cannot be its own parent")
    for k, v in data.items():
        setattr(cat, k, v)
    audit(session, "category.update", "category", cat.id, admin.id)
    await session.commit()
    return CategoryOut.model_validate({**{k: getattr(cat, k) for k in CategoryOut.model_fields if k != "children"},
                                       "children": []})


# --- Reviews ----------------------------------------------------------------------
@router.get("/reviews", response_model=list[ReviewOut])
async def reviews(status: str = "pending", limit: int = Query(50, le=200), session: AsyncSession = Depends(get_session)):
    return (await session.execute(select(Review).where(Review.status == ReviewStatus(status))
                                  .order_by(Review.created_at.desc()).limit(limit))).scalars().all()


@router.post("/reviews/{review_id}/moderate", response_model=ReviewOut)
async def moderate(review_id: int, approve: bool, reason: str | None = None, admin: User = Depends(admin_user),
                   session: AsyncSession = Depends(get_session)):
    try:
        return await review_service.moderate_review(session, admin, review_id, approve, reason)
    except review_service.ReviewError as exc:
        raise HTTPException(404, str(exc)) from exc


# --- Reports ----------------------------------------------------------------------
@router.get("/reports")
async def reports(status: str = "open", session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(Report).where(Report.status == ReportStatus(status))
                                  .order_by(Report.created_at.desc()).limit(100))).scalars().all()
    return [{"id": r.id, "target_type": r.target_type.value, "target_id": r.target_id, "reason": r.reason,
             "status": r.status.value, "reporter_id": r.reporter_id, "created_at": r.created_at} for r in rows]


@router.post("/reports/{report_id}")
async def resolve_report(report_id: int, status: str, note: str | None = None, admin: User = Depends(admin_user),
                         session: AsyncSession = Depends(get_session)):
    try:
        r = await admin_service.resolve_report(session, admin, report_id, ReportStatus(status), note)
    except (admin_service.AdminError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"id": r.id, "status": r.status.value}


# --- Bookings ---------------------------------------------------------------------
@router.get("/bookings")
async def bookings(status: str | None = None, limit: int = Query(50, le=200), offset: int = 0,
                   session: AsyncSession = Depends(get_session)):
    stmt = select(Booking)
    if status:
        stmt = stmt.where(Booking.status == BookingStatus(status))
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = (await session.execute(stmt.order_by(Booking.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    return page([BookingOut.model_validate(b) for b in rows], total)


# --- Monetisation -----------------------------------------------------------------
class PlanIn(BaseModel):
    code: str
    name: str
    price_cents_monthly: int = 0
    commission_bps: int = 0
    ranking_boost: float = 0.0
    features: dict = {}
    is_active: bool = True


def _plan(p: Plan) -> dict:
    return {"id": p.id, "code": p.code, "name": p.name, "price_cents_monthly": p.price_cents_monthly,
            "commission_bps": p.commission_bps, "ranking_boost": p.ranking_boost, "features": p.features,
            "is_active": p.is_active}


@router.get("/plans")
async def plans(session: AsyncSession = Depends(get_session)):
    return [_plan(p) for p in (await session.execute(select(Plan).order_by(Plan.price_cents_monthly))).scalars()]


@router.post("/plans", status_code=201)
async def upsert_plan(body: PlanIn, admin: User = Depends(admin_user), session: AsyncSession = Depends(get_session)):
    plan = (await session.execute(select(Plan).where(Plan.code == body.code))).scalar_one_or_none()
    if plan is None:
        plan = Plan(**body.model_dump())
        session.add(plan)
    else:
        for k, v in body.model_dump().items():
            setattr(plan, k, v)
    audit(session, "plan.upsert", "plan", body.code, admin.id)
    await session.commit()
    return _plan(plan)


@router.get("/settings/{key}")
async def get_setting(key: str, session: AsyncSession = Depends(get_session)):
    return await admin_service.get_setting(session, key)


@router.put("/settings/{key}")
async def put_setting(key: str, value: dict, admin: User = Depends(admin_user),
                      session: AsyncSession = Depends(get_session)):
    return await admin_service.put_setting(session, admin, key, value)


@router.get("/audit")
async def audit_log(limit: int = Query(100, le=500), session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit))).scalars().all()
    return [{"id": a.id, "actor_user_id": a.actor_user_id, "action": a.action, "entity": a.entity,
             "entity_id": a.entity_id, "data": a.data, "created_at": a.created_at} for a in rows]
