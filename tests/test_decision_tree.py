import pytest
from qualsynth.models import StudyInput, Quote, Theme
from qualsynth.decision_tree import analyse_decision_tree


@pytest.fixture
def classified_studies():
    """Studies with distinct textual content and theme assignments."""
    studies = [
        StudyInput(
            study_id="S1", title="Identity and diabetes",
            authors="A et al.", year=2020,
            key_findings=["diabetes identity disruption self-concept change"],
            quotes=[Quote(quote_id="q1", text="identity shifted after diagnosis")],
        ),
        StudyInput(
            study_id="S2", title="Daily management burden",
            authors="B et al.", year=2021,
            key_findings=["daily burden management fatigue exhaustion"],
            quotes=[Quote(quote_id="q2", text="tired of managing every day")],
        ),
        StudyInput(
            study_id="S3", title="Social tensions in diabetes",
            authors="C et al.", year=2019,
            key_findings=["social navigation family tension meals culture"],
            quotes=[Quote(quote_id="q3", text="family meals create social tension")],
        ),
        StudyInput(
            study_id="S4", title="Empowerment through knowledge",
            authors="D et al.", year=2022,
            key_findings=["knowledge empowerment monitoring control anxiety"],
            quotes=[Quote(quote_id="q4", text="knowledge empowers self monitoring")],
        ),
        StudyInput(
            study_id="S5", title="Identity crisis in chronic illness",
            authors="E et al.", year=2021,
            key_findings=["identity crisis chronic illness self-concept"],
            quotes=[Quote(quote_id="q5", text="chronic illness changes identity")],
        ),
    ]
    themes = [
        Theme(theme_id="T1", label="Identity disruption",
              assigned_studies=["S1", "S5"]),
        Theme(theme_id="T2", label="Daily burden",
              assigned_studies=["S2"]),
        Theme(theme_id="T3", label="Social navigation",
              assigned_studies=["S3"]),
        Theme(theme_id="T4", label="Empowerment",
              assigned_studies=["S4"]),
    ]
    return studies, themes


def test_oob_error_range(classified_studies):
    """OOB error must be in [0, 1]."""
    studies, themes = classified_studies
    result = analyse_decision_tree(studies, themes, seed=42)
    assert 0.0 <= result["oob_error"] <= 1.0, (
        f"OOB error {result['oob_error']} out of range"
    )


def test_predictions_cover_all_assigned(classified_studies):
    """Predictions must include every study that has a theme assignment."""
    studies, themes = classified_studies
    result = analyse_decision_tree(studies, themes, seed=42)
    assigned_ids = set()
    for t in themes:
        assigned_ids.update(t.assigned_studies)
    for sid in assigned_ids:
        assert sid in result["predictions"], f"Missing prediction for {sid}"


def test_feature_importance_non_negative(classified_studies):
    """All feature importance values must be >= 0."""
    studies, themes = classified_studies
    result = analyse_decision_tree(studies, themes, seed=42)
    for word, val in result["feature_importance"].items():
        assert val >= -1e-9, f"Negative importance {val} for {word}"


def test_loo_accuracy_range(classified_studies):
    """LOO accuracy must be in [0, 1]."""
    studies, themes = classified_studies
    result = analyse_decision_tree(studies, themes, seed=42)
    assert 0.0 <= result["loo_accuracy"] <= 1.0, (
        f"LOO accuracy {result['loo_accuracy']} out of range"
    )


def test_top_features_length(classified_studies):
    """Top features list must have at most 10 entries."""
    studies, themes = classified_studies
    result = analyse_decision_tree(studies, themes, seed=42)
    assert len(result["top_features"]) <= 10
