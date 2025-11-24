"""
Segmentation policy model.

Defines how Ethernet frames are segmented into FSO payload segments.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# PUBLIC_INTERFACE
class SegmentationPolicy(BaseModel):
    """Segmentation policy to guide frame segmentation."""
    max_segment_size: int = Field(1200, ge=256, le=9216, description="Max payload bytes per segment.")
    align_to: int = Field(1, ge=1, le=256, description="Optional alignment for segment sizes in bytes.")
    include_crc32: bool = Field(True, description="Include CRC32 per segment.")
    arq_enabled: bool = Field(True, description="Attach ARQ metadata in headers.")
    fec_scheme: str | None = Field(None, description="FEC scheme identifier or None.")

    def normalized_size(self, requested: int | None = None) -> int:
        """Return normalized segment size aligned to 'align_to' boundary."""
        size = requested or self.max_segment_size
        if size < 256:
            size = 256
        if size > 9216:
            size = 9216
        # align
        if self.align_to > 1:
            rem = size % self.align_to
            if rem:
                size = size - rem
        return size
