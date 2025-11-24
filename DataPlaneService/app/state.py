"""
Application state module for DataPlaneService.

Holds singletons that should be shared across routers, such as the
EncapsulationService instance, to maintain queues and statistics.
"""
from __future__ import annotations

from typing import Optional
from .services.encapsulation_service import EncapsulationService

_encapsulation_service: Optional[EncapsulationService] = None


# PUBLIC_INTERFACE
def get_encapsulation_service() -> EncapsulationService:
    """Return the shared EncapsulationService singleton instance."""
    global _encapsulation_service
    if _encapsulation_service is None:
        _encapsulation_service = EncapsulationService()
    return _encapsulation_service
