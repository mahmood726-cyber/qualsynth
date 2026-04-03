import pytest
from qualsynth.models import StudyInput, Quote, Theme
from qualsynth.fuzzy_sets import (
    compute_membership_matrix,
    compute_cardinalities,
    compute_fuzzy_similarity,
    compute_fuzzy_entropy,
    compute_theme_sharpness,
    analyse_fuzzy_sets,
)


@pytest.fixture
def fuzzy_studies():
    """Studies with quotes for fuzzy membership testing."""
    return [
        StudyInput(
            study_id="S1", title="Study One", authors="A", year=2020,
            quality_score="high",
            key_findings=["identity disruption after diagnosis"],
            quotes=[
                Quote(quote_id="Q1", text="I felt lost"),
                Quote(quote_id="Q2", text="Everything changed"),
            ],
        ),
        StudyInput(
            study_id="S2", title="Study Two", authors="B", year=2021,
            quality_score="moderate",
            key_findings=["daily burden of management", "social tension"],
            quotes=[
                Quote(quote_id="Q3", text="It's exhausting"),
                Quote(quote_id="Q4", text="Family doesn't understand"),
            ],
        ),
        StudyInput(
            study_id="S3", title="Study Three", authors="C", year=2022,
            quality_score="low",
            key_findings=["empowerment through knowledge"],
            quotes=[
                Quote(quote_id="Q5", text="Knowledge is power"),
            ],
        ),
    ]


@pytest.fixture
def fuzzy_themes():
    """Themes with assigned quotes and studies."""
    return [
        Theme(
            theme_id="T1", label="Identity disruption",
            assigned_quotes=["Q1", "Q2"],
            assigned_studies=["S1", "S2"],
            concepts=["identity", "self"],
        ),
        Theme(
            theme_id="T2", label="Daily burden",
            assigned_quotes=["Q3"],
            assigned_studies=["S2", "S3"],
            concepts=["burden", "management"],
        ),
        Theme(
            theme_id="T3", label="Social navigation",
            assigned_quotes=["Q4", "Q5"],
            assigned_studies=["S1"],
            concepts=["social", "family"],
        ),
    ]


def test_membership_in_01(fuzzy_studies, fuzzy_themes):
    """All fuzzy membership values must be in [0, 1]."""
    mm = compute_membership_matrix(fuzzy_studies, fuzzy_themes)
    for key, mu in mm.items():
        assert 0.0 <= mu <= 1.0, f"mu={mu} out of [0,1] for {key}"


def test_cardinalities_nonnegative(fuzzy_studies, fuzzy_themes):
    """Fuzzy cardinalities must be >= 0."""
    mm = compute_membership_matrix(fuzzy_studies, fuzzy_themes)
    cards = compute_cardinalities(mm, fuzzy_themes)
    for tid, c in cards.items():
        assert c >= 0.0, f"Cardinality {c} negative for {tid}"


def test_fuzzy_similarity_in_01(fuzzy_studies, fuzzy_themes):
    """Fuzzy Jaccard similarity must be in [0, 1]."""
    mm = compute_membership_matrix(fuzzy_studies, fuzzy_themes)
    fsim = compute_fuzzy_similarity(mm, fuzzy_studies, fuzzy_themes)
    for key, val in fsim.items():
        assert 0.0 <= val <= 1.0 + 1e-9, f"Similarity {val} out of [0,1] for {key}"


def test_fuzzy_entropy_in_01(fuzzy_studies, fuzzy_themes):
    """Fuzzy entropy per theme must be in [0, 1]."""
    mm = compute_membership_matrix(fuzzy_studies, fuzzy_themes)
    fe = compute_fuzzy_entropy(mm, fuzzy_studies, fuzzy_themes)
    for tid, e in fe.items():
        assert 0.0 <= e <= 1.0 + 1e-9, f"Entropy {e} out of [0,1] for {tid}"


def test_sharpness_plus_entropy_is_one(fuzzy_studies, fuzzy_themes):
    """Theme sharpness + fuzzy entropy should equal 1.0 for each theme."""
    result = analyse_fuzzy_sets(fuzzy_studies, fuzzy_themes)
    for tid in result["theme_entropy"]:
        total = result["theme_entropy"][tid] + result["theme_sharpness"][tid]
        assert abs(total - 1.0) < 1e-9, f"entropy + sharpness = {total} for {tid}"
