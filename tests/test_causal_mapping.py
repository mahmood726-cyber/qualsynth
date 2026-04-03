import pytest
from qualsynth.models import StudyInput, Quote, Theme
from qualsynth.causal_mapping import analyse_causal_map


@pytest.fixture
def causal_studies():
    """Studies with explicit causal language for causal mapping."""
    return [
        StudyInput(
            study_id="S1", title="Stress and burnout",
            authors="Doe A", year=2020, methodology="phenomenology",
            key_findings=[
                "Work pressure leads to emotional exhaustion.",
                "Exhaustion contributes to isolation from peers.",
                "Isolation increases anxiety.",
            ],
            quotes=[
                Quote(quote_id="Q1",
                      text="The workload causes so much stress."),
            ],
        ),
        StudyInput(
            study_id="S2", title="Support systems",
            authors="Roe B", year=2021, methodology="grounded_theory",
            key_findings=[
                "Peer support reduces isolation.",
                "Management support prevents burnout.",
                "Support enables recovery and wellbeing.",
            ],
            quotes=[
                Quote(quote_id="Q2",
                      text="Having colleagues who understand facilitates coping."),
            ],
        ),
    ]


@pytest.fixture
def causal_themes():
    """Themes with concepts matching causal study content."""
    return [
        Theme(theme_id="T1", label="Work pressure",
              concepts=["workload", "pressure", "stress"],
              assigned_studies=["S1", "S2"]),
        Theme(theme_id="T2", label="Emotional exhaustion",
              concepts=["exhaustion", "burnout", "fatigue"],
              assigned_studies=["S1"]),
        Theme(theme_id="T3", label="Social isolation",
              concepts=["isolation", "loneliness", "withdrawal"],
              assigned_studies=["S1", "S2"]),
        Theme(theme_id="T4", label="Peer support",
              concepts=["support", "colleagues", "peers"],
              assigned_studies=["S2"]),
    ]


def test_causal_edges_have_valid_themes(causal_studies, causal_themes):
    """Every causal edge must reference themes that exist in the input."""
    result = analyse_causal_map(causal_studies, causal_themes)
    valid_ids = {t.theme_id for t in causal_themes}
    for edge in result["causal_edges"]:
        assert edge["cause_theme"] in valid_ids, (
            f"Cause theme {edge['cause_theme']} not in valid themes"
        )
        assert edge["effect_theme"] in valid_ids, (
            f"Effect theme {edge['effect_theme']} not in valid themes"
        )


def test_edge_direction_valid(causal_studies, causal_themes):
    """Each causal edge direction must be '+' or '-'."""
    result = analyse_causal_map(causal_studies, causal_themes)
    for edge in result["causal_edges"]:
        assert edge["direction"] in ("+", "-"), (
            f"Invalid direction {edge['direction']}"
        )


def test_n_causal_claims_non_negative(causal_studies, causal_themes):
    """Number of causal claims must be non-negative."""
    result = analyse_causal_map(causal_studies, causal_themes)
    assert result["n_causal_claims"] >= 0


def test_causal_density_in_range(causal_studies, causal_themes):
    """Causal density must be in [0, 1]."""
    result = analyse_causal_map(causal_studies, causal_themes)
    assert 0.0 <= result["causal_density"] <= 1.0 + 1e-9, (
        f"Causal density {result['causal_density']} out of range"
    )


def test_leverage_scores_non_negative(causal_studies, causal_themes):
    """All leverage point scores must be non-negative."""
    result = analyse_causal_map(causal_studies, causal_themes)
    for item in result["leverage_themes"]:
        assert item["score"] >= 0.0, (
            f"Leverage score {item['score']} is negative for {item['theme_id']}"
        )
