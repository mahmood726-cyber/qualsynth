import pytest
from qualsynth.models import Theme, StudyInput
from qualsynth.bayesian_saturation import estimate_theme_richness


@pytest.fixture
def richness_themes():
    """Themes with varying study frequencies for richness estimation."""
    return [
        Theme(theme_id="T1", label="Common theme",
              assigned_studies=["S1", "S2", "S3", "S4", "S5"]),
        Theme(theme_id="T2", label="Moderate theme",
              assigned_studies=["S1", "S3", "S5"]),
        Theme(theme_id="T3", label="Rare theme A",
              assigned_studies=["S2"]),
        Theme(theme_id="T4", label="Rare theme B",
              assigned_studies=["S4"]),
        Theme(theme_id="T5", label="Doubleton theme",
              assigned_studies=["S1", "S3"]),
    ]


@pytest.fixture
def richness_studies():
    """Five studies for the richness estimation fixtures."""
    return [
        StudyInput(study_id="S1", title="Study 1", authors="A", year=2020),
        StudyInput(study_id="S2", title="Study 2", authors="B", year=2021),
        StudyInput(study_id="S3", title="Study 3", authors="C", year=2022),
        StudyInput(study_id="S4", title="Study 4", authors="D", year=2023),
        StudyInput(study_id="S5", title="Study 5", authors="E", year=2024),
    ]


def test_chao1_geq_observed(richness_themes, richness_studies):
    """Chao1 estimate must be >= number of observed themes."""
    result = estimate_theme_richness(richness_themes, richness_studies)
    s_obs = len([t for t in richness_themes
                 if any(sid in [s.study_id for s in richness_studies]
                        for sid in t.assigned_studies)])
    assert result["chao1_estimate"] >= s_obs - 1e-9


def test_coverage_range(richness_themes, richness_studies):
    """Coverage must be in [0, 1]."""
    result = estimate_theme_richness(richness_themes, richness_studies)
    assert 0.0 - 1e-9 <= result["coverage"] <= 1.0 + 1e-9


def test_rarefaction_monotonic(richness_themes, richness_studies):
    """Rarefaction curve must be non-decreasing (more studies -> more themes)."""
    result = estimate_theme_richness(richness_themes, richness_studies)
    curve = result["rarefaction_curve"]
    for i in range(1, len(curve)):
        assert curve[i]["expected_themes"] >= curve[i - 1]["expected_themes"] - 1e-9, (
            f"Rarefaction decreased from m={curve[i-1]['m']} to m={curve[i]['m']}"
        )


def test_good_turing_p_new_range(richness_themes, richness_studies):
    """Good-Turing probability of new theme must be in [0, 1]."""
    result = estimate_theme_richness(richness_themes, richness_studies)
    assert 0.0 - 1e-9 <= result["good_turing_p_new"] <= 1.0 + 1e-9


def test_unseen_nonnegative(richness_themes, richness_studies):
    """Estimated unseen themes must be >= 0."""
    result = estimate_theme_richness(richness_themes, richness_studies)
    assert result["unseen_estimate"] >= 0.0 - 1e-9
    # CI lower bound should be <= upper bound
    lo, hi = result["chao1_ci"]
    assert lo <= hi + 1e-9
