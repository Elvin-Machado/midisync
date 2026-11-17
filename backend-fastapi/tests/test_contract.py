"""Module A0 verification: the shared data contract."""
import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from pydantic import ValidationError

from app.contract import CanonicalScan

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "contract" / "scan.schema.json").read_text())
CANONICAL = json.loads((ROOT / "contract" / "examples" / "canonical_emergency.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def schema_ok(doc) -> bool:
    return VALIDATOR.is_valid(doc)


def pydantic_ok(doc) -> bool:
    try:
        CanonicalScan.model_validate(doc)
        return True
    except ValidationError:
        return False


def test_schema_is_valid_draft_2020_12():
    Draft202012Validator.check_schema(SCHEMA)


def test_canonical_passes_both_validators():
    VALIDATOR.validate(CANONICAL)
    CanonicalScan.model_validate(CANONICAL)


def test_pydantic_roundtrip_is_byte_identical():
    scan = CanonicalScan.model_validate(CANONICAL)
    assert json.loads(scan.model_dump_json()) == CANONICAL


def test_required_fields_match_between_schema_and_model():
    assert set(SCHEMA["required"]) == set(CanonicalScan.model_fields)
    assert set(SCHEMA["properties"]["vitals"]["required"]) == set(
        CanonicalScan.model_fields["vitals"].annotation.model_fields
    )


def _mutate(path, value):
    doc = copy.deepcopy(CANONICAL)
    *parents, leaf = path
    node = doc
    for p in parents:
        node = node[p]
    if value is _DELETE:
        del node[leaf]
    else:
        node[leaf] = value
    return doc


_DELETE = object()

BAD_CASES = {
    "missing vitals": (["vitals"], _DELETE),
    "spo2 > 100": (["vitals", "spo2"], 101),
    "hr as string": (["vitals", "hr"], "142"),
    "unknown triage": (["triage_state"], "CRITICAL"),
    "unknown data_mode": (["data_mode"], "REPLAY"),
    "confidence > 1": (["tinyml_confidence"], 1.2),
    "battery < 0": (["battery_pct"], -1),
    "bad device id": (["device_id"], "k1"),
    "non-UTC timestamp": (["recorded_at"], "2026-11-17T10:35:00+05:30"),
    "lowercase symptom": (["patient", "symptoms"], ["chest_pain"]),
    "duplicate symptom": (["patient", "symptoms"], ["CHEST_PAIN", "CHEST_PAIN"]),
    "adc sample > 12-bit": (["ecg_samples"], [5000]),
    "extra top-level field": (["patient_name"], "John"),
    "extra vitals field": (["vitals", "bp"], 120),
}


@pytest.mark.parametrize("name", BAD_CASES)
def test_invalid_docs_rejected_by_both(name):
    doc = _mutate(*BAD_CASES[name])
    assert not schema_ok(doc), f"schema accepted: {name}"
    assert not pydantic_ok(doc), f"pydantic accepted: {name}"


def test_event_id_must_match_device_id():
    doc = _mutate(["event_id"], "K02-1794891900")
    assert not pydantic_ok(doc)
