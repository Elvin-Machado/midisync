"""Short codes shared by the offline QR format and every component.

Firmware (C) must carry an identical copy of these tables.
"""

# QR "sym" code -> canonical symptom
SYMPTOM_CODES: dict[str, str] = {
    "CP": "CHEST_PAIN",
    "BR": "BREATHLESSNESS",
    "FV": "FEVER",
    "UC": "UNCONSCIOUS",
    "SZ": "SEIZURE",
    "BL": "BLEEDING",
    "DZ": "DIZZINESS",
    "VM": "VOMITING",
    "HA": "HEADACHE",
    "AP": "ABDOMINAL_PAIN",
    "WK": "WEAKNESS",
    "CF": "CONFUSION",
    "PL": "PALPITATIONS",
    "SW": "SWEATING",
}
SYMPTOM_TO_CODE = {v: k for k, v in SYMPTOM_CODES.items()}

# QR "tri" code -> canonical triage_state
TRIAGE_CODES: dict[str, str] = {"EMERG": "EMERGENCY", "URG": "URGENT", "STAB": "STABLE"}
TRIAGE_TO_CODE = {v: k for k, v in TRIAGE_CODES.items()}

AGE_BANDS = ("0-5", "6-17", "18-39", "40-59", "60+")


def age_to_band(age: int) -> str:
    if age <= 5:
        return "0-5"
    if age <= 17:
        return "6-17"
    if age <= 39:
        return "18-39"
    if age <= 59:
        return "40-59"
    return "60+"
