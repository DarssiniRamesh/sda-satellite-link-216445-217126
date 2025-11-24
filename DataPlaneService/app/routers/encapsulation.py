"""
Encapsulation router: APIs to encapsulate Ethernet frames into FSO segments
and to dequeue TX and RX segments.

Swagger/OpenAPI docs included per endpoint.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..models.frame_spec import (
    EncapsulationRequest,
    EncapsulationResponse,
    EncapsulatedSegment,
)
from ..services.encapsulation_service import EncapsulationService


router = APIRouter(prefix="/encapsulation", tags=["encapsulation"])


# Note: Do not wrap service instances inside Pydantic models. FastAPI dependency
# injection via Depends(get_service) is used to provide the EncapsulationService.
# This avoids including arbitrary service types in OpenAPI/Pydantic schemas.


def get_service() -> EncapsulationService:
    # In a production system, this would come from app state or DI container.
    from ..state import get_encapsulation_service
    return get_encapsulation_service()


# PUBLIC_INTERFACE
@router.post(
    "/pack",
    response_model=EncapsulationResponse,
    summary="Encapsulate Ethernet frame",
    description="Splits a hex-encoded Ethernet frame into FSO segments according to the segmentation policy.",
    responses={
        200: {"description": "Encapsulation successful"},
        400: {"description": "Invalid input"},
        500: {"description": "Internal error"},
    },
)
def pack(req: EncapsulationRequest, svc: EncapsulationService = Depends(get_service)) -> EncapsulationResponse:
    """Encapsulate an Ethernet frame into FSO segments."""
    # Basic sanity checks before heavy processing
    if not req.ethernet_frame_hex or len(req.ethernet_frame_hex) % 2 != 0:
        raise HTTPException(status_code=400, detail="ethernet_frame_hex must be non-empty even-length hex")
    if req.max_segment_size < 256 or req.max_segment_size > 9216:
        raise HTTPException(status_code=400, detail="max_segment_size must be within 256..9216")
    try:
        return svc.encapsulate(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# PUBLIC_INTERFACE
@router.get(
    "/tx/dequeue",
    response_model=list[EncapsulatedSegment],
    summary="Dequeue TX segments",
    description="Returns up to N pending segments queued for transmit.",
)
def tx_dequeue(n: int = 10, svc: EncapsulationService = Depends(get_service)) -> list[EncapsulatedSegment]:
    """Dequeue up to n segments from TX queue."""
    if n <= 0 or n > 1000:
        raise HTTPException(status_code=400, detail="n must be in 1..1000")
    return svc.dequeue_tx(n)


# PUBLIC_INTERFACE
@router.get(
    "/rx/dequeue",
    response_model=list[EncapsulatedSegment],
    summary="Dequeue RX segments",
    description="Returns up to N received segments queued from the receiver side.",
)
def rx_dequeue(n: int = 10, svc: EncapsulationService = Depends(get_service)) -> list[EncapsulatedSegment]:
    """Dequeue up to n segments from RX queue."""
    if n <= 0 or n > 1000:
        raise HTTPException(status_code=400, detail="n must be in 1..1000")
    return svc.dequeue_rx(n)
