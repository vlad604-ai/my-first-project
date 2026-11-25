"""Client <-> professional messaging relayed through the platform (no phone number leak)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Message, Professional, Report, ReportTarget, User
from app.services import notifications

UTC = timezone.utc
MAX_MESSAGES_PER_HOUR = 30


class MessagingError(Exception):
    pass


async def send_message(session: AsyncSession, sender: User, client_id: int, pro_id: int, body: str) -> Message:
    body = (body or "").strip()
    if not body:
        raise MessagingError("empty")
    pro = (await session.execute(select(Professional).where(Professional.id == pro_id)
                                 .options(selectinload(Professional.user)))).scalar_one_or_none()
    if pro is None:
        raise MessagingError("unknown_professional")
    if sender.id not in (client_id, pro.user_id):
        raise MessagingError("not_a_participant")
    if sender.is_banned:
        raise MessagingError("banned")
    recent = await session.scalar(select(func.count(Message.id)).where(
        Message.sender_user_id == sender.id, Message.created_at > datetime.now(UTC) - timedelta(hours=1)))
    if recent >= MAX_MESSAGES_PER_HOUR:
        raise MessagingError("rate_limited")
    msg = Message(client_id=client_id, professional_id=pro_id, sender_user_id=sender.id, body=body[:3000])
    session.add(msg)
    await session.commit()
    if sender.id == client_id:
        await notifications.new_message(pro.user, sender.display_name, body, f"msg:pro:{client_id}")
    else:
        client = await session.get(User, client_id)
        if client:
            await notifications.new_message(client, pro.business_name, body, f"msg:cli:{pro_id}")
    return msg


async def thread(session: AsyncSession, client_id: int, pro_id: int, limit: int = 20) -> list[Message]:
    rows = await session.execute(select(Message).where(Message.client_id == client_id,
                                                       Message.professional_id == pro_id)
                                 .order_by(Message.created_at.desc()).limit(limit))
    return list(reversed(rows.scalars().all()))


async def report(session: AsyncSession, reporter: User, target_type: ReportTarget, target_id, reason: str) -> Report:
    rep = Report(reporter_id=reporter.id, target_type=target_type, target_id=str(target_id), reason=reason[:2000])
    session.add(rep)
    await session.commit()
    return rep
