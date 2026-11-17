"""Pydantic mirror of contract/scan.schema.json.

tests/test_contract.py asserts the two stay in sync, so change both together.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator

AdcSample = Annotated[int, Field(strict=True, ge=0, le=4095)]
Symptom = Literal[
    "CHEST_PAIN",
    "BREATHLESSNESS",
    "FEVER",
    "UNCONSCIOUS",
    "SEIZURE",
    "BLEEDING",
    "DIZZINESS",
    "VOMITING",
    "HEADACHE",
    "ABDOMINAL_PAIN",
    "WEAKNESS",
    "CONFUSION",
    "PALPITATIONS",
    "SWEATING",
]


class DataMode(str, Enum):
    LIVE = "LIVE"
    SIMULATED = "SIMULATED"


class TriageState(str, Enum):
    EMERGENCY = "EMERGENCY"
    URGENT = "URGENT"
    STABLE = "STABLE"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Patient(_Strict):
    age_band: Literal["0-5", "6-17", "18-39", "40-59", "60+"]
    gender: Literal["M", "F", "O"]
    symptoms: list[Symptom] = Field(max_length=16)

    @field_validator("symptoms")
    @classmethod
    def _unique(cls, v: list[str]) -> list[str]:
        if len(set(v)) != len(v):
            raise ValueError("symptoms must be unique")
        return v


class Vitals(_Strict):
    hr: int = Field(strict=True, ge=0, le=300)
    spo2: int = Field(strict=True, ge=0, le=100)
    temp: float = Field(strict=True, ge=25, le=45)
    gsr: float = Field(strict=True, ge=0)
    emg: float = Field(strict=True, ge=0)
    sqi_valid: bool = Field(strict=True)


class CanonicalScan(_Strict):
    event_id: str = Field(pattern=r"^[A-Z][0-9]{2}-[0-9]{10}$")
    referral_id: str = Field(pattern=r"^R[0-9]{4}$")
    device_id: str = Field(pattern=r"^[A-Z][0-9]{2}$")
    recorded_at: datetime
    battery_pct: int = Field(strict=True, ge=0, le=100)
    data_mode: DataMode
    triage_state: TriageState
    trigger_reason: str = Field(max_length=120)
    tinyml_confidence: float = Field(strict=True, ge=0, le=1)
    patient: Patient
    vitals: Vitals
    ecg_samples: list[AdcSample] = Field(max_length=2048)
    emg_samples: list[AdcSample] = Field(max_length=2048)

    @field_validator("recorded_at")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset().total_seconds() != 0:
            raise ValueError("recorded_at must be UTC ('Z')")
        return v.astimezone(timezone.utc)

    @model_validator(mode="after")
    def _event_id_prefix(self) -> "CanonicalScan":
        if not self.event_id.startswith(f"{self.device_id}-"):
            raise ValueError("event_id must start with '<device_id>-'")
        return self

    @field_serializer("recorded_at")
    def _ser_ts(self, v: datetime) -> str:
        return v.strftime("%Y-%m-%dT%H:%M:%SZ")
