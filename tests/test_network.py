import pytest
from qualsynth.models import Theme
from qualsynth.network import analyse_theme_network


@pytest.fixture
def connected_themes():
    """Five themes with overlapping study assignments for network analysis."""
    return [
        Theme(theme_id="T1", label="Identity disruption",
              assigned_studies=["S1", "S2", "S3", "S4"]),
        Theme(theme_id="T2", label="Daily burden",
              assigned_studies=["S1", "S2", "S5"]),
        Theme(theme_id="T3", label="Social navigation",
              assigned_studies=["S3", "S4", "S5"]),
        Theme(theme_id="T4", label="Empowerment",
              assigned_studies=["S2", "S5"]),
        Theme(theme_id="T5", label="Isolation",
              assigned_studies=["S6"]),
    ]


def test_cooccurrence_symmetric(connected_themes):
    """Co-occurrence matrix must be symmetric."""
    result = analyse_theme_network(connected_themes)
    matrix = result["co_occurrence_matrix"]
    k = len(connected_themes)
    for i in range(k):
        for j in range(k):
            assert matrix[i][j] == matrix[j][i]


def test_degree_centrality_range(connected_themes):
    """Degree centrality must be in [0, 1] for all themes."""
    result = analyse_theme_network(connected_themes)
    for tid, val in result["degree_centrality"].items():
        assert 0.0 - 1e-9 <= val <= 1.0 + 1e-9, (
            f"Degree centrality {val} out of range for {tid}"
        )


def test_betweenness_centrality_range(connected_themes):
    """Betweenness centrality must be in [0, 1] for all themes."""
    result = analyse_theme_network(connected_themes)
    for tid, val in result["betweenness_centrality"].items():
        assert 0.0 - 1e-9 <= val <= 1.0 + 1e-9, (
            f"Betweenness centrality {val} out of range for {tid}"
        )


def test_closeness_centrality_range(connected_themes):
    """Closeness centrality must be >= 0 for all themes."""
    result = analyse_theme_network(connected_themes)
    for tid, val in result["closeness_centrality"].items():
        assert val >= 0.0 - 1e-9, (
            f"Closeness centrality {val} negative for {tid}"
        )


def test_communities_cover_all_themes(connected_themes):
    """Every theme must appear in exactly one community."""
    result = analyse_theme_network(connected_themes)
    all_ids = set()
    for comm in result["communities"]:
        for tid in comm:
            assert tid not in all_ids, f"{tid} appears in multiple communities"
            all_ids.add(tid)
    expected = {t.theme_id for t in connected_themes}
    assert all_ids == expected
