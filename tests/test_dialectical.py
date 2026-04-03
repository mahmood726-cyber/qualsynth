import pytest
from qualsynth.models import StudyInput, Theme
from qualsynth.dialectical import analyse_dialectical


@pytest.fixture
def dialectical_studies():
    """Studies with mixed positive and negative findings for dialectical analysis."""
    return [
        StudyInput(
            study_id="S1", title="Study 1", authors="A", year=2020,
            key_findings=[
                "The intervention was effective and showed clear benefit.",
                "Support from staff facilitated positive outcomes.",
            ],
        ),
        StudyInput(
            study_id="S2", title="Study 2", authors="B", year=2021,
            key_findings=[
                "Multiple barriers and challenges hindered implementation.",
                "Participants found the process difficult and limiting.",
            ],
        ),
        StudyInput(
            study_id="S3", title="Study 3", authors="C", year=2022,
            key_findings=[
                "Despite initial challenges, effective support enabled improvement.",
                "The programme overcame barriers through helpful peer networks.",
            ],
        ),
    ]


@pytest.fixture
def dialectical_themes():
    """Themes with contrasting polarities and a bridging synthesis theme."""
    return [
        Theme(theme_id="T1", label="Benefits",
              assigned_studies=["S1"]),
        Theme(theme_id="T2", label="Barriers",
              assigned_studies=["S2"]),
        Theme(theme_id="T3", label="Resolution through support",
              assigned_studies=["S1", "S2", "S3"]),
    ]


def test_polarities_in_range(dialectical_studies, dialectical_themes):
    """All theme polarities must be in [-1, 1]."""
    result = analyse_dialectical(dialectical_studies, dialectical_themes)
    for tid, pol in result["theme_polarities"].items():
        assert -1.0 <= pol <= 1.0, f"Polarity {pol} out of range for {tid}"


def test_antithetical_pairs_detected(dialectical_studies, dialectical_themes):
    """At least one antithetical pair should be detected with opposing themes."""
    result = analyse_dialectical(dialectical_studies, dialectical_themes)
    assert len(result["antithetical_pairs"]) >= 1
    for pair in result["antithetical_pairs"]:
        assert "thesis" in pair
        assert "antithesis" in pair
        assert pair["strength"] > 0


def test_dialectical_depth_in_range(dialectical_studies, dialectical_themes):
    """Dialectical depth must be in [0, 1]."""
    result = analyse_dialectical(dialectical_studies, dialectical_themes)
    assert 0.0 <= result["dialectical_depth"] <= 1.0


def test_resolution_score_in_range(dialectical_studies, dialectical_themes):
    """Resolution score must be in [0, 1]."""
    result = analyse_dialectical(dialectical_studies, dialectical_themes)
    assert 0.0 <= result["resolution_score"] <= 1.0


def test_contradiction_matrix_covers_pairs(dialectical_studies, dialectical_themes):
    """Contradiction matrix must have an entry for every theme pair."""
    result = analyse_dialectical(dialectical_studies, dialectical_themes)
    n_themes = len(dialectical_themes)
    expected_pairs = n_themes * (n_themes - 1) // 2
    assert len(result["contradiction_matrix"]) == expected_pairs
    valid_relationships = {"concordant", "contradictory", "synthesized"}
    for key, rel in result["contradiction_matrix"].items():
        assert rel in valid_relationships, f"Invalid relationship: {rel}"
