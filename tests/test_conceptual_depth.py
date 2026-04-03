import pytest
from qualsynth.conceptual_depth import analyse_conceptual_depth


def test_hermeneutic_depth_in_range(diabetes_studies, diabetes_themes):
    """Hermeneutic depth index must be in [0, 1]."""
    result = analyse_conceptual_depth(diabetes_studies, diabetes_themes)
    hdi = result["hermeneutic_depth_index"]
    assert 0.0 <= hdi <= 1.0, f"HDI {hdi} out of [0,1] range"


def test_abstraction_levels_in_range(diabetes_studies, diabetes_themes):
    """All theme abstraction levels must be in [1, 4]."""
    result = analyse_conceptual_depth(diabetes_studies, diabetes_themes)
    for theme_id, level in result["theme_levels"].items():
        assert 1 <= level <= 4, f"Theme {theme_id} level {level} out of [1,4]"


def test_level_distribution_sums(diabetes_studies, diabetes_themes):
    """Level distribution counts must sum to total number of themes."""
    result = analyse_conceptual_depth(diabetes_studies, diabetes_themes)
    total = sum(result["level_distribution"].values())
    assert total == len(diabetes_themes)


def test_theoretical_reach_range(diabetes_studies, diabetes_themes):
    """Theoretical reach must be in [0, 1]."""
    result = analyse_conceptual_depth(diabetes_studies, diabetes_themes)
    tr = result["theoretical_reach"]
    assert 0.0 <= tr <= 1.0, f"Theoretical reach {tr} out of [0,1]"


def test_development_correlation_range(diabetes_studies, diabetes_themes):
    """Development correlation must be in [-1, 1]."""
    result = analyse_conceptual_depth(diabetes_studies, diabetes_themes)
    corr = result["development_correlation"]
    assert -1.0 <= corr <= 1.0 + 1e-9, f"Correlation {corr} out of [-1,1]"
    # Mean abstraction must be >= 1.0 (minimum level)
    assert result["mean_abstraction"] >= 1.0
