"""Account API routes."""

from __future__ import annotations

from fastapi import APIRouter

from qts.api.mappers import map_account_snapshot_dto
from qts.api.schemas.common import AccountSnapshotSchema
from qts.application.services import AccountQueryService

router = APIRouter(prefix="/accounts")

# No live account source is bound to this stateless API process; the service
# derives an honest empty cash snapshot when an account has no bound source.
_accounts = AccountQueryService()


@router.get("/{account_id}", response_model=AccountSnapshotSchema)
def account_snapshot(account_id: str) -> AccountSnapshotSchema:
    """Return an account snapshot from the account query service."""
    return map_account_snapshot_dto(_accounts.account_snapshot(account_id))


__all__ = ["router"]
