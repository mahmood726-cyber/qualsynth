import pytest
from qualsynth.reflexivity import compute_reflexivity
from qualsynth.models import Theme, StudyInput, TranslationMatrix, TranslationCell


def test_overall_score_range(diabetes_studies, diabetes_themes):
    """Overall reflexivity score must be in [0, 1]."""
    result = compute_reflexivity(diabetes_studies, diabetes_themes)
    assert 0.0 <= result["overall_score"] <= 1.0


def test_all_indicators_range(diabetes_studies, diabetes_themes):
    """Each of the 6 indicators must be in [0, 1]."""
    result = compute_reflexivity(diabetes_studies, diabetes_themes)
    assert len(result["indicators"]) == 6
    for key, val in result["indicators"].items():
        assert 0.0 <= val <= 1.0, f"{key} = {val} out of range"


def test_rating_values(diabetes_studies, diabetes_themes):
    """Rating must be one of Green, Amber, Red."""
    result = compute_reflexivity(diabetes_studies, diabetes_themes)
    assert result["rating"] in ("Green", "Amber", "Red")


def test_empty_themes_gives_red():
    """No themes should produce a Red rating."""
    studies = [
        StudyInput(study_id="S1", title="Test", authors="A", year=2020),
        StudyInput(study_id="S2", title="Test2", authors="B", year=2021),
    ]
    result = compute_reflexivity(studies, [])
    assert result["overall_score"] == 0.0
    assert result["rating"] == "Red"


def test_recommendations_for_low_indicators():
    """Low-scoring indicators should generate recommendations."""
    studies = [
        StudyInput(study_id="S1", title="Test", authors="A", year=2020),
        StudyInput(study_id="S2", title="Test2", authors="B", year=2021),
    ]
    themes = [
        Theme(
            theme_id="T1", label="Only theme", level="descriptive",
            assigned_quotes=["Q1"], assigned_studies=["S1"],
            concepts=["concept_a"],
        ),
    ]
    result = compute_reflexivity(studies, themes)
    # S2 not covered, no analytical themes, no refutational concepts
    assert len(result["recommendations"]) > 0
    assert result["overall_score"] < 0.7
