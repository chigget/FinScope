
import quality_store


def test_save_and_update_quality_report(
    tmp_path, monkeypatch
):

    # Use a temporary database
    test_db = tmp_path / "test.db"

    monkeypatch.setattr(
        quality_store,
        "DB_PATH",
        test_db
    )

    cik = "0000320193"

    issues = [{
        "severity": "WARNING",
        "code": "MISSING_YEAR",
        "year": 2023,
        "message": "Missing annual data"
    }]

    # Save the first report
    quality_store.save_quality_report(cik, issues)

    report = quality_store.get_quality_report(cik)

    assert report is not None
    assert report["issues"] == issues
    assert report["checked_at"]

    # Update report with no findings
    quality_store.save_quality_report(cik, [])

    updated = quality_store.get_quality_report(cik)

    assert updated["issues"] == []
