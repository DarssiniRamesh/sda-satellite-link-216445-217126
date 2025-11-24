"""
Buffers router: endpoints for interacting with RX buffer (e.g., pushing received segments).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..models.frame_spec import EncapsulatedSegment
# Do not import or annotate with EncapsulationService to prevent Pydantic schema generation attempts.

router = APIRouter(prefix="/buffers", tags=["buffers"])


def get_service():
    from ..state import get_encapsulation_service
    return get_encapsulation_service()


# PUBLIC_INTERFACE
@router.post(
    "/rx/push",
    summary="Push received segment",
    description="Push a received segment from lower layers into the RX queue and reassembly buffers.",
    responses={202: {"description": "Accepted"}, 400: {"description": "Invalid segment"}},
    status_code=202,
)
def push_rx(seg: EncapsulatedSegment, svc = Depends(get_service)) -> dict:
    """Push a received segment into RX queue."""
    try:
        svc.accept_rx_segment(seg)
    except Exception as exc:  # safety net: don't leak internals
        raise HTTPException(status_code=400, detail="Invalid segment") from exc
    return {"status": "accepted"}
