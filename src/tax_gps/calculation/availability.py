"""Availability of new-cash planning, distinct from baseline tax readiness."""

from enum import StrEnum


class PlanningAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    BASELINE_NOT_READY = "BASELINE_NOT_READY"
    PVD_BASELINE_ONLY = "PVD_BASELINE_ONLY"
    RMF_BASELINE_ONLY = "RMF_BASELINE_ONLY"
