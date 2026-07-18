"""Transform raw API JSON into flat rows for PostgreSQL."""

from __future__ import annotations

from typing import Any


def _get(module: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    if not module:
        return default
    value: Any = module
    for key in keys:
        if not isinstance(value, dict):
            return default
        value = value.get(key)
    return default if value is None else value


def _date_string(date_struct: dict[str, Any] | None) -> str | None:
    """Return YYYY-MM-DD for PostgreSQL, or None if date is partial/invalid."""
    if not date_struct:
        return None
    raw = date_struct.get("date")
    if not raw or len(raw) < 10:
        return None
    return raw[:10]


def parse_study(study: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Parse one study into trial + related rows."""
    protocol = study.get("protocolSection", {})

    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {})
    design = protocol.get("designModule", {})
    conditions = protocol.get("conditionsModule", {})
    locations_module = protocol.get("contactsLocationsModule", {})

    nct_id = identification.get("nctId")
    if not nct_id:
        return {"trials": [], "conditions": [], "phases": [], "locations": []}

    enrollment = design.get("enrollmentInfo", {})
    lead_sponsor = sponsor.get("leadSponsor", {})

    trial_row = {
        "nct_id": nct_id,
        "brief_title": identification.get("briefTitle"),
        "official_title": identification.get("officialTitle"),
        "overall_status": status.get("overallStatus"),
        "study_type": design.get("studyType"),
        "sponsor_name": lead_sponsor.get("name"),
        "sponsor_class": lead_sponsor.get("class"),
        "start_date": _date_string(status.get("startDateStruct")),
        "primary_completion_date": _date_string(status.get("primaryCompletionDateStruct")),
        "completion_date": _date_string(status.get("completionDateStruct")),
        "enrollment_count": enrollment.get("count"),
    }

    condition_rows = [
        {"nct_id": nct_id, "condition": condition}
        for condition in conditions.get("conditions", [])
        if condition
    ]

    phase_rows = [
        {"nct_id": nct_id, "phase": phase}
        for phase in design.get("phases", [])
        if phase
    ]

    location_rows = []
    for location in locations_module.get("locations", []):
        country = location.get("country")
        if not country:
            continue
        location_rows.append(
            {
                "nct_id": nct_id,
                "country": country,
                "city": location.get("city"),
                "state": location.get("state"),
            }
        )

    return {
        "trials": [trial_row],
        "conditions": condition_rows,
        "phases": phase_rows,
        "locations": location_rows,
    }
