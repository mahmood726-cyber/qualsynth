import pytest
from qualsynth.argument_mining import extract_arguments


def test_argument_units_non_empty(diabetes_studies, diabetes_themes):
    """Argument units must be non-empty for real study data."""
    result = extract_arguments(diabetes_studies, diabetes_themes)
    assert len(result["argument_units"]) > 0
    # Each unit must have text, type, and study_id
    for unit in result["argument_units"]:
        assert "text" in unit and len(unit["text"]) > 0
        assert unit["type"] in ("claim", "evidence", "reasoning")
        assert "study_id" in unit and len(unit["study_id"]) > 0


def test_total_counts_consistent(diabetes_studies, diabetes_themes):
    """Total claims + evidence + reasoning must equal total units."""
    result = extract_arguments(diabetes_studies, diabetes_themes)
    total = result["total_claims"] + result["total_evidence"] + result["total_reasoning"]
    assert total == len(result["argument_units"])
    assert total > 0


def test_theme_arguments_all_themes_present(diabetes_studies, diabetes_themes):
    """theme_arguments must have an entry for every theme."""
    result = extract_arguments(diabetes_studies, diabetes_themes)
    for theme in diabetes_themes:
        assert theme.theme_id in result["theme_arguments"]
        args = result["theme_arguments"][theme.theme_id]
        assert "claims" in args
        assert "evidence" in args
        assert "reasoning" in args


def test_argument_strength_non_negative(diabetes_studies, diabetes_themes):
    """Argument strength must be non-negative for all themes."""
    result = extract_arguments(diabetes_studies, diabetes_themes)
    for theme_id, strength in result["argument_strength"].items():
        assert strength >= 0.0, f"Negative strength for {theme_id}: {strength}"


def test_support_relations_structure(burnout_studies, burnout_data):
    """Support relations must have from, to, and type fields."""
    themes = burnout_data[1]
    result = extract_arguments(burnout_studies, themes)
    for rel in result["support_relations"]:
        assert "from" in rel
        assert "to" in rel
        assert rel["type"] in ("supports", "refutes")
        assert rel["from"] != rel["to"], "Self-relation not allowed"
