from tests.fixtures import SAMPLE_STUDY
from etl.transform import parse_study


def test_parse_study_extracts_core_fields():
    parsed = parse_study(SAMPLE_STUDY)
    trial = parsed["trials"][0]

    assert trial["nct_id"] == "NCT00000001"
    assert trial["brief_title"] == "Test Study"
    assert trial["overall_status"] == "RECRUITING"
    assert trial["sponsor_class"] == "INDUSTRY"
    assert trial["enrollment_count"] == 500
    assert trial["start_date"] == "2024-01-15"


def test_parse_study_extracts_conditions():
    parsed = parse_study(SAMPLE_STUDY)
    conditions = [r["condition"] for r in parsed["conditions"]]
    assert "Breast Cancer" in conditions
    assert len(parsed["conditions"]) == 2


def test_parse_study_extracts_phases_and_locations():
    parsed = parse_study(SAMPLE_STUDY)
    phases = [r["phase"] for r in parsed["phases"]]
    countries = [r["country"] for r in parsed["locations"]]

    assert phases == ["PHASE2", "PHASE3"]
    assert "United States" in countries
    assert "Germany" in countries


def test_parse_study_skips_missing_nct_id():
    parsed = parse_study({"protocolSection": {"identificationModule": {}}})
    assert parsed["trials"] == []
