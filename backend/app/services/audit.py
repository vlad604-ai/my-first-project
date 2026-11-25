from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


def audit(session: AsyncSession, action: str, entity: str, entity_id=None, actor_id: int | None = None, **data) -> None:
    """Append an audit log entry to the current transaction."""
    session.add(
        AuditLog(
            actor_user_id=actor_id,
            action=action,
            entity=entity,
            entity_id=str(entity_id) if entity_id is not None else None,
            data={k: (str(v) if not isinstance(v, (int, float, bool, type(None), list, dict)) else v) for k, v in data.items()},
        )
    )
