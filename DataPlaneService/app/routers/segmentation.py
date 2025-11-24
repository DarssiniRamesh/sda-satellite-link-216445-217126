"""
Segmentation/reassembly router: APIs to reassemble Ethernet frames from segments.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..models.frame_spec import (
    ReassemblyRequest,
    ReassemblyResponse,
)
from ..services.encapsulation_service import EncapsulationService

router = APIRouter(prefix="/segmentation", tags=["segmentation"])


def get_service() -> EncapsulationService:
    from ..state import get_encapsulation_service
    return get_encapsulation_service()


# PUBLIC_INTERFACE
@router.post(
    "/reassemble",
    response_model=ReassemblyResponse,
    summary="Reassemble Ethernet frame",
    description="Reassembles a full Ethernet frame from provided FSO segments. Returns status 'complete' or 'partial' with missing indices.",
    responses={
        200: {"description": "Reassembly result"},
        400: {"description": "Invalid request"},
    },
)
def reassemble(req: ReassemblyRequest, svc: EncapsulationService = Depends(get_service)) -> ReassemblyResponse:
    """Reassemble Ethernet frame from segments."""
    if not req.segments:
        raise HTTPException(status_code=400, detail="segments array must not be empty")
    return svc.reassemble(req)
