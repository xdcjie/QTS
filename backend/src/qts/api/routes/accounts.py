"""Account API routes."""

from __future__ import annotations

from fastapi import APIRouter

from qts.api.schemas.common import AccountSnapshotSchema

router = APIRouter(prefix="/accounts")


@router.get("/{account_id}", response_model=AccountSnapshotSchema)
def account_snapshot(account_id: str) -> AccountSnapshotSchema:
    return AccountSnapshotSchema(account_id=account_id, cash={"USD": "0"})


__all__ = ["router"]
