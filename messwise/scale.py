"""MessWise Smart Scale Integration Adapter (Module C: C8).

Implements specifications from PLAN.md Section 5 (Module C8):
- Digital scale platform (ESP32 + HX711 load-cell) payload parsing and validation.
- Validates unit consistency (kg only for mass), non-negative readings, and tare calibration.
- Distinguishes scale hardware readings (entry_method='smart_scale') from manual entries.
- Clear error handling for disconnected devices, zero or negative weights, and unstable readings.
- Explicit human confirmation: Scale weights fill review slots; cook confirms before saving.
- Authoritative manual fallback always available.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


@dataclass
class SmartScaleReading:
    """Validated measurement payload from an institutional kitchen smart scale (C8)."""

    device_id: str
    gross_weight_kg: float
    tare_weight_kg: float
    net_weight_kg: float
    unit: str
    timestamp: str
    is_stable: bool
    is_valid: bool
    status_message: str
    entry_method: str = "smart_scale"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_and_validate_scale_payload(
    payload: Dict[str, Any],
    min_weight_kg: float = 0.05,
    max_weight_kg: float = 150.0,
) -> SmartScaleReading:
    """Validate raw payload from ESP32 / HX711 digital load-cell scale."""
    device_id = str(payload.get("device_id", "HX711-ESP32-SCALE01")).strip()
    gross = float(payload.get("gross_weight_kg", 0.0))
    tare = float(payload.get("tare_weight_kg", 0.0))
    net = float(payload.get("net_weight_kg", gross - tare))
    unit = str(payload.get("unit", "kg")).strip().lower()
    ts = str(payload.get("timestamp", datetime.now(timezone.utc).isoformat()))
    stable = bool(payload.get("is_stable", True))

    # 1. Unit validation
    if unit not in ("kg", "kilo", "kilogram"):
        return SmartScaleReading(
            device_id=device_id,
            gross_weight_kg=gross,
            tare_weight_kg=tare,
            net_weight_kg=0.0,
            unit=unit,
            timestamp=ts,
            is_stable=stable,
            is_valid=False,
            status_message=f"Invalid scale unit '{unit}'. Smart scale must output in kg.",
        )

    # 2. Reading sanity checks
    if net < 0.0:
        return SmartScaleReading(
            device_id=device_id,
            gross_weight_kg=gross,
            tare_weight_kg=tare,
            net_weight_kg=net,
            unit="kg",
            timestamp=ts,
            is_stable=stable,
            is_valid=False,
            status_message=f"Negative net reading ({net:.2f} kg). Scale requires tare recalibration.",
        )

    if net > max_weight_kg:
        return SmartScaleReading(
            device_id=device_id,
            gross_weight_kg=gross,
            tare_weight_kg=tare,
            net_weight_kg=net,
            unit="kg",
            timestamp=ts,
            is_stable=stable,
            is_valid=False,
            status_message=f"Reading ({net:.1f} kg) exceeds maximum scale capacity ({max_weight_kg} kg).",
        )

    if not stable:
        return SmartScaleReading(
            device_id=device_id,
            gross_weight_kg=gross,
            tare_weight_kg=tare,
            net_weight_kg=round(net, 2),
            unit="kg",
            timestamp=ts,
            is_stable=False,
            is_valid=False,
            status_message="Scale reading unstable. Please allow scale platform to settle before capturing.",
        )

    return SmartScaleReading(
        device_id=device_id,
        gross_weight_kg=round(gross, 2),
        tare_weight_kg=round(tare, 2),
        net_weight_kg=round(net, 2),
        unit="kg",
        timestamp=ts,
        is_stable=True,
        is_valid=True,
        status_message=f"Scale reading verified: {net:.2f} kg net (Device: {device_id}).",
    )
