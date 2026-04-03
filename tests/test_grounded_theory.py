"""Tests for grounded_theory.py — computational grounded theory."""

import pytest
from qualsynth.models import Theme
from qualsynth.grounded_theory import run_grounded_theory


def test_open_codes_frequency_ge2(diabetes_studies, diabetes_themes):
    """All open codes must have frequency >= 2 (appear in at least 2 studies)."""
    result = run_grounded_theory(diabetes_studies, diabetes_themes)
    for code in result["open_codes"]:
        assert code["frequency"] >= 2, (
            f"Code '{code['text']}' has frequency {code['frequency']}, expected >= 2"
        )


def test_core_category_non_empty(diabetes_studies, diabetes_themes):
    """Core category should be a non-empty string when codes exist."""
    result = run_grounded_theory(diabetes_studies, diabetes_themes)
    if result["axial_categories"]:
        assert result["core_category"], "Core category should not be empty"
        assert isinstance(result["core_category"], str)


def test_axial_categories_contain_codes(diabetes_studies, diabetes_themes):
    """Each axial category must contain at least one code."""
    result = run_grounded_theory(diabetes_studies, diabetes_themes)
    for cat in result["axial_categories"]:
        assert len(cat["codes"]) >= 1, (
            f"Category '{cat['label']}' has no codes"
        )
        assert cat["n_studies"] >= 2, (
            f"Category '{cat['label']}' has {cat['n_studies']} studies, expected >= 2"
        )


def test_comparison_matrix_jaccard_range(diabetes_studies, diabetes_themes):
    """Jaccard similarity in comparison matrix must be in [0, 1]."""
    result = run_grounded_theory(diabetes_studies, diabetes_themes)
    for key, comp in result["comparison_matrix"].items():
        assert 0.0 <= comp["similarity"] <= 1.0, (
            f"Jaccard {comp['similarity']} out of [0,1] for {key}"
        )
        assert comp["overlap"] >= 0
        assert comp["divergence"] >= 0


def test_merge_candidates_high_similarity(diabetes_studies, diabetes_themes):
    """All merge candidates must have similarity > 0.7."""
    result = run_grounded_theory(diabetes_studies, diabetes_themes)
    for mc in result["merge_candidates"]:
        assert mc["similarity"] > 0.7, (
            f"Merge candidate {mc} has similarity <= 0.7"
        )
