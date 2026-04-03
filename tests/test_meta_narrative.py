import pytest
from qualsynth.models import StudyInput, Quote, Theme
from qualsynth.meta_narrative import (
    analyse_meta_narrative,
    _edit_distance,
    _normalized_similarity,
)


@pytest.fixture
def narrative_studies():
    """Studies spanning different years and methodological traditions."""
    return [
        StudyInput(
            study_id="S1", title="Early qualitative exploration",
            authors="Alpha A", year=2010, methodology="phenomenology",
            key_findings=[
                "Identity disruption was the dominant experience.",
                "Social navigation shaped daily coping.",
            ],
            quotes=[
                Quote(quote_id="Q1", text="It changed who I am."),
            ],
        ),
        StudyInput(
            study_id="S2", title="Mid-period grounded theory",
            authors="Beta B", year=2015, methodology="grounded_theory",
            key_findings=[
                "Identity disruption persisted over time.",
                "Daily burden emerged as a core category.",
                "Social navigation remained important.",
            ],
            quotes=[
                Quote(quote_id="Q2", text="Every day is a battle."),
            ],
        ),
        StudyInput(
            study_id="S3", title="Recent ethnography",
            authors="Gamma C", year=2020, methodology="ethnography",
            key_findings=[
                "Empowerment through knowledge was key.",
                "Technology reduced daily burden.",
            ],
            quotes=[
                Quote(quote_id="Q3", text="Knowledge is power."),
            ],
        ),
        StudyInput(
            study_id="S4", title="Divergent tradition",
            authors="Delta D", year=2022, methodology="case_study",
            key_findings=[
                "Empowerment through collective action.",
                "Knowledge exchange within communities.",
            ],
            quotes=[
                Quote(quote_id="Q4", text="We learn from each other."),
            ],
        ),
    ]


@pytest.fixture
def narrative_themes():
    """Themes with assigned studies spanning the narrative studies."""
    return [
        Theme(theme_id="T1", label="Identity disruption",
              concepts=["identity", "self"],
              assigned_studies=["S1", "S2"]),
        Theme(theme_id="T2", label="Daily burden",
              concepts=["burden", "fatigue", "daily"],
              assigned_studies=["S2", "S3"]),
        Theme(theme_id="T3", label="Social navigation",
              concepts=["social", "family", "navigation"],
              assigned_studies=["S1", "S2"]),
        Theme(theme_id="T4", label="Empowerment through knowledge",
              concepts=["empowerment", "knowledge", "technology"],
              assigned_studies=["S3", "S4"]),
    ]


def test_edit_distance_symmetric():
    """Levenshtein edit distance must be symmetric."""
    a = ["T1", "T2", "T3"]
    b = ["T1", "T3"]
    assert _edit_distance(a, b) == _edit_distance(b, a)


def test_normalized_similarity_range():
    """Normalized similarity must be in [0, 1]."""
    a = ["T1", "T2", "T3"]
    b = ["T4", "T5"]
    sim = _normalized_similarity(a, b)
    assert 0.0 - 1e-9 <= sim <= 1.0 + 1e-9


def test_clusters_cover_all_studies(narrative_studies, narrative_themes):
    """Every study must appear in exactly one cluster."""
    result = analyse_meta_narrative(narrative_studies, narrative_themes)
    all_study_ids = set()
    for cluster in result["clusters"]:
        for sid in cluster["studies"]:
            assert sid not in all_study_ids, (
                f"Study {sid} appears in multiple clusters"
            )
            all_study_ids.add(sid)
    expected = {s.study_id for s in narrative_studies}
    assert all_study_ids == expected


def test_similarity_matrix_symmetric(narrative_studies, narrative_themes):
    """Narrative similarity matrix must be symmetric."""
    result = analyse_meta_narrative(narrative_studies, narrative_themes)
    mat = result["narrative_similarity_matrix"]
    study_ids = [s.study_id for s in narrative_studies]
    for si in study_ids:
        for sj in study_ids:
            assert abs(mat[(si, sj)] - mat[(sj, si)]) < 1e-9, (
                f"Asymmetry between ({si},{sj}) and ({sj},{si})"
            )


def test_incommensurability_in_range(narrative_studies, narrative_themes):
    """Incommensurability index must be in [0, 1]."""
    result = analyse_meta_narrative(narrative_studies, narrative_themes)
    idx = result["incommensurability_index"]
    assert 0.0 - 1e-9 <= idx <= 1.0 + 1e-9, (
        f"Incommensurability index {idx} out of range"
    )
