import pytest
from qualsynth.themes import (
    create_theme, assign_quote, merge_themes, compute_saturation,
    get_study_coverage, build_theme_stats,
)
from qualsynth.models import Theme


def test_create_theme():
    t = create_theme("T1", "Burden", description="Daily management burden")
    assert t.theme_id == "T1"
    assert t.label == "Burden"
    assert t.level == "descriptive"


def test_assign_quote():
    t = Theme(theme_id="T1", label="Burden")
    t = assign_quote(t, "Q1", "Study1")
    assert "Q1" in t.assigned_quotes
    assert "Study1" in t.assigned_studies


def test_assign_quote_no_duplicate():
    t = Theme(theme_id="T1", label="Burden")
    t = assign_quote(t, "Q1", "Study1")
    t = assign_quote(t, "Q1", "Study1")
    assert t.assigned_quotes.count("Q1") == 1


def test_merge_themes():
    t1 = Theme(theme_id="T1", label="A", assigned_quotes=["Q1"], assigned_studies=["S1"])
    t2 = Theme(theme_id="T2", label="B", assigned_quotes=["Q2"], assigned_studies=["S2"])
    merged = merge_themes("T3", "A+B", [t1, t2])
    assert set(merged.assigned_quotes) == {"Q1", "Q2"}
    assert set(merged.assigned_studies) == {"S1", "S2"}


def test_saturation(diabetes_studies, diabetes_themes):
    for theme in diabetes_themes:
        if theme.level == "descriptive":
            sat = compute_saturation(theme, len(diabetes_studies))
            assert 0.0 <= sat <= 1.0


def test_build_theme_stats(diabetes_themes, diabetes_studies):
    stats = build_theme_stats(diabetes_themes, len(diabetes_studies))
    assert len(stats) == len(diabetes_themes)
    for s in stats:
        assert "label" in s
        assert "n_quotes" in s
        assert "saturation" in s
