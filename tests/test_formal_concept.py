import pytest
from qualsynth.models import StudyInput, Theme
from qualsynth.formal_concept import analyse_formal_concepts


@pytest.fixture
def fca_studies():
    """Simple studies for FCA testing."""
    return [
        StudyInput(study_id="S1", title="Study 1", authors="A", year=2020,
                   key_findings=["Finding 1"]),
        StudyInput(study_id="S2", title="Study 2", authors="B", year=2021,
                   key_findings=["Finding 2"]),
        StudyInput(study_id="S3", title="Study 3", authors="C", year=2022,
                   key_findings=["Finding 3"]),
    ]


@pytest.fixture
def fca_themes():
    """Themes with overlapping study assignments for lattice structure."""
    return [
        Theme(theme_id="T1", label="Theme A",
              assigned_studies=["S1", "S2", "S3"]),
        Theme(theme_id="T2", label="Theme B",
              assigned_studies=["S1", "S2"]),
        Theme(theme_id="T3", label="Theme C",
              assigned_studies=["S2", "S3"]),
    ]


def test_n_concepts_at_least_one(fca_studies, fca_themes):
    """Concept lattice must contain at least one formal concept."""
    result = analyse_formal_concepts(fca_studies, fca_themes)
    assert result["n_concepts"] >= 1


def test_concepts_have_extent_and_intent(fca_studies, fca_themes):
    """Each concept must have extent (studies) and intent (themes) lists."""
    result = analyse_formal_concepts(fca_studies, fca_themes)
    for concept in result["concepts"]:
        assert "extent" in concept
        assert "intent" in concept
        assert isinstance(concept["extent"], list)
        assert isinstance(concept["intent"], list)


def test_hasse_edges_reference_valid_indices(fca_studies, fca_themes):
    """All Hasse diagram edges must reference valid concept indices."""
    result = analyse_formal_concepts(fca_studies, fca_themes)
    n = result["n_concepts"]
    for edge in result["hasse_edges"]:
        assert 0 <= edge["parent"] < n
        assert 0 <= edge["child"] < n
        assert edge["parent"] != edge["child"]


def test_lattice_width_positive(fca_studies, fca_themes):
    """Lattice width (max antichain) must be at least 1."""
    result = analyse_formal_concepts(fca_studies, fca_themes)
    assert result["lattice_width"] >= 1


def test_implications_valid_structure(fca_studies, fca_themes):
    """Implications must have antecedent, consequent, and positive support."""
    result = analyse_formal_concepts(fca_studies, fca_themes)
    theme_ids = {t.theme_id for t in fca_themes}
    for impl in result["implications"]:
        assert "antecedent" in impl
        assert "consequent" in impl
        assert "support" in impl
        assert impl["support"] > 0
        assert impl["consequent"] in theme_ids
        for a in impl["antecedent"]:
            assert a in theme_ids
