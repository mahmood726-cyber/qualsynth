import pytest
from qualsynth.synthesis import build_soqf_table, build_theme_summary


def test_soqf_table(diabetes_findings):
    from qualsynth.cerqual import assess_cerqual
    assessed = [assess_cerqual(f) for f in diabetes_findings]
    table = build_soqf_table(assessed)
    assert len(table) == len(diabetes_findings)
    for row in table:
        assert "finding" in row
        assert "confidence" in row
        assert "n_studies" in row


def test_theme_summary(diabetes_themes, diabetes_studies):
    summary = build_theme_summary(diabetes_themes, diabetes_studies)
    assert "n_descriptive" in summary
    assert "n_analytical" in summary
    assert summary["n_descriptive"] >= 0


def test_soqf_confidence_populated(diabetes_findings):
    from qualsynth.cerqual import assess_cerqual
    assessed = [assess_cerqual(f) for f in diabetes_findings]
    table = build_soqf_table(assessed)
    for row in table:
        assert row["confidence"] in ("High", "Moderate", "Low", "Very Low")
