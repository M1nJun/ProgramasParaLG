from __future__ import annotations

from vision.base import VisionAdapter
from vision.welding.adapter import WeldingAdapter
from vision.lead.adapter import LeadAdapter


def get_adapter(vision_mode: str) -> VisionAdapter:
    v = (vision_mode or "").strip().lower()
    if v == "welding":
        return WeldingAdapter()
    if v == "lead":
        return LeadAdapter()
    raise ValueError(f"Unknown vision_mode: {vision_mode!r}")