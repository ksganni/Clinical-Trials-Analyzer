SAMPLE_STUDY = {
    "protocolSection": {
        "identificationModule": {
            "nctId": "NCT00000001",
            "briefTitle": "Test Study",
            "officialTitle": "Official Test Study Title",
        },
        "statusModule": {
            "overallStatus": "RECRUITING",
            "startDateStruct": {"date": "2024-01-15"},
            "primaryCompletionDateStruct": {"date": "2025-06-01"},
            "completionDateStruct": {"date": "2025-12-01"},
        },
        "sponsorCollaboratorsModule": {
            "leadSponsor": {"name": "Pfizer", "class": "INDUSTRY"}
        },
        "designModule": {
            "studyType": "INTERVENTIONAL",
            "phases": ["PHASE2", "PHASE3"],
            "enrollmentInfo": {"count": 500},
        },
        "conditionsModule": {
            "conditions": ["Breast Cancer", "Oncology"]
        },
        "contactsLocationsModule": {
            "locations": [
                {"country": "United States", "city": "Boston", "state": "Massachusetts"},
                {"country": "Germany", "city": "Berlin"},
            ]
        },
    }
}
