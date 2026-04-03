import pytest
from qualsynth.models import StudyInput, Quote, Theme
from qualsynth.information_retrieval import (
    compute_precision,
    compute_recall,
    compute_f1,
    compute_ndcg,
    compute_auc_roc,
    analyse_information_retrieval,
)
from qualsynth.fuzzy_sets import compute_membership_matrix


@pytest.fixture
def ir_studies():
    """Studies with varied quality scores for IR testing."""
    return [
        StudyInput(
            study_id="S1", title="High quality study", authors="A", year=2020,
            quality_score="high",
            key_findings=["important finding"],
            quotes=[Quote(quote_id="Q1", text="strong evidence")],
        ),
        StudyInput(
            study_id="S2", title="Moderate study", authors="B", year=2021,
            quality_score="moderate",
            key_findings=["moderate finding"],
            quotes=[Quote(quote_id="Q2", text="some evidence")],
        ),
        StudyInput(
            study_id="S3", title="Low quality study", authors="C", year=2022,
            quality_score="low",
            key_findings=["weak finding"],
            quotes=[Quote(quote_id="Q3", text="limited evidence")],
        ),
        StudyInput(
            study_id="S4", title="Another high study", authors="D", year=2023,
            quality_score="high",
            key_findings=["another finding"],
            quotes=[Quote(quote_id="Q4", text="more evidence")],
        ),
    ]


@pytest.fixture
def ir_themes():
    """Themes with assigned studies for IR testing."""
    return [
        Theme(
            theme_id="T1", label="Main theme",
            assigned_studies=["S1", "S2"],
            assigned_quotes=["Q1", "Q2"],
            concepts=["evidence"],
        ),
        Theme(
            theme_id="T2", label="Secondary theme",
            assigned_studies=["S3"],
            assigned_quotes=["Q3"],
            concepts=["limited"],
        ),
        Theme(
            theme_id="T3", label="Broad theme",
            assigned_studies=["S1", "S2", "S3", "S4"],
            assigned_quotes=["Q1", "Q2", "Q3", "Q4"],
            concepts=["finding"],
        ),
    ]


def test_f1_in_01(ir_studies, ir_themes):
    """F1 score must be in [0, 1] for all themes."""
    prec = compute_precision(ir_themes, ir_studies)
    rec = compute_recall(ir_themes, ir_studies)
    f1 = compute_f1(prec, rec)
    for tid, val in f1.items():
        assert 0.0 <= val <= 1.0 + 1e-9, f"F1={val} out of [0,1] for {tid}"


def test_ndcg_in_01(ir_studies, ir_themes):
    """NDCG must be in [0, 1] for all themes."""
    ndcg = compute_ndcg(ir_themes, ir_studies)
    for tid, val in ndcg.items():
        assert 0.0 <= val <= 1.0 + 1e-9, f"NDCG={val} out of [0,1] for {tid}"


def test_auc_in_01(ir_studies, ir_themes):
    """AUC-ROC must be in [0, 1] for all themes."""
    mm = compute_membership_matrix(ir_studies, ir_themes)
    auc = compute_auc_roc(ir_themes, ir_studies, mm)
    for tid, val in auc.items():
        assert 0.0 <= val <= 1.0 + 1e-9, f"AUC={val} out of [0,1] for {tid}"


def test_map_in_01(ir_studies, ir_themes):
    """MAP score must be in [0, 1]."""
    result = analyse_information_retrieval(ir_studies, ir_themes)
    assert 0.0 <= result["map_score"] <= 1.0 + 1e-9


def test_full_analysis_keys(ir_studies, ir_themes):
    """Full IR analysis must return all expected keys."""
    mm = compute_membership_matrix(ir_studies, ir_themes)
    result = analyse_information_retrieval(ir_studies, ir_themes, mm)
    expected_keys = {"precision", "recall", "f1", "map_score", "ndcg", "auc_roc", "mean_auc"}
    assert set(result.keys()) == expected_keys
