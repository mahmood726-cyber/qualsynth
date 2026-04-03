import pytest
from qualsynth.models import StudyInput, Quote, Theme
from qualsynth.temporal_analysis import (
    compute_emergence_timeline,
    compute_growth_curves,
    compute_co_evolution,
    build_influence_graph,
    analyse_temporal,
)


@pytest.fixture
def temporal_studies():
    """Studies spanning multiple years for temporal analysis."""
    return [
        StudyInput(
            study_id="S1", title="Early study", authors="A", year=2010,
            quality_score="high",
            key_findings=["first finding"],
            quotes=[Quote(quote_id="Q1", text="early evidence")],
        ),
        StudyInput(
            study_id="S2", title="Mid study", authors="B", year=2015,
            quality_score="moderate",
            key_findings=["second finding"],
            quotes=[Quote(quote_id="Q2", text="mid evidence")],
        ),
        StudyInput(
            study_id="S3", title="Recent study", authors="C", year=2020,
            quality_score="high",
            key_findings=["third finding"],
            quotes=[Quote(quote_id="Q3", text="recent evidence")],
        ),
        StudyInput(
            study_id="S4", title="Latest study", authors="D", year=2022,
            quality_score="moderate",
            key_findings=["fourth finding"],
            quotes=[Quote(quote_id="Q4", text="latest evidence")],
        ),
    ]


@pytest.fixture
def temporal_themes():
    """Themes with studies from different years."""
    return [
        Theme(
            theme_id="T1", label="Established theme",
            assigned_studies=["S1", "S2", "S3"],
            assigned_quotes=["Q1", "Q2", "Q3"],
            concepts=["evidence"],
        ),
        Theme(
            theme_id="T2", label="Emerging theme",
            assigned_studies=["S3", "S4"],
            assigned_quotes=["Q3", "Q4"],
            concepts=["recent"],
        ),
        Theme(
            theme_id="T3", label="Old theme",
            assigned_studies=["S1"],
            assigned_quotes=["Q1"],
            concepts=["early"],
        ),
    ]


def test_emergence_year_within_range(temporal_studies, temporal_themes):
    """Emergence year must be <= max study year for each theme."""
    max_year = max(s.year for s in temporal_studies)
    emergence = compute_emergence_timeline(temporal_themes, temporal_studies)
    for tid, year in emergence.items():
        if year is not None:
            assert year <= max_year, f"Emergence year {year} > max {max_year} for {tid}"


def test_growth_curve_monotonic(temporal_studies, temporal_themes):
    """Growth curves must be monotonically non-decreasing."""
    growth = compute_growth_curves(temporal_themes, temporal_studies)
    for tid, curve in growth.items():
        for i in range(1, len(curve)):
            assert curve[i]["cumulative"] >= curve[i - 1]["cumulative"], (
                f"Growth curve not monotonic for {tid} at year {curve[i]['year']}"
            )


def test_co_evolution_in_range(temporal_studies, temporal_themes):
    """Temporal co-evolution correlations must be in [-1, 1]."""
    coevo = compute_co_evolution(temporal_themes, temporal_studies)
    for key, corr in coevo.items():
        assert -1.0 - 1e-9 <= corr <= 1.0 + 1e-9, (
            f"Correlation {corr} out of [-1,1] for {key}"
        )


def test_influence_scores_nonnegative(temporal_studies, temporal_themes):
    """Influence scores (out-degree) must be >= 0."""
    edges, scores = build_influence_graph(temporal_themes, temporal_studies)
    for sid, score in scores.items():
        assert score >= 0, f"Influence score {score} negative for {sid}"


def test_full_temporal_keys(temporal_studies, temporal_themes):
    """Full temporal analysis must return all expected keys."""
    result = analyse_temporal(temporal_studies, temporal_themes)
    expected_keys = {
        "emergence_timeline", "growth_curves", "temporal_diversity",
        "innovation_rate", "paradigm_shifts", "influence_scores", "co_evolution",
    }
    assert set(result.keys()) == expected_keys
