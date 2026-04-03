"""Tests for partial_order.py — partial order and lattice analysis of themes."""

import pytest
from qualsynth.models import Theme
from qualsynth.partial_order import analyse_partial_order


@pytest.fixture
def hierarchical_themes():
    """Themes with clear subsumption: T1 covers all studies,
    T2 and T3 are subsets of T1, T4 is a subset of T2."""
    return [
        Theme(theme_id="T1", label="Broad theme",
              assigned_studies=["S1", "S2", "S3", "S4", "S5"]),
        Theme(theme_id="T2", label="Medium theme A",
              assigned_studies=["S1", "S2", "S3"]),
        Theme(theme_id="T3", label="Medium theme B",
              assigned_studies=["S4", "S5"]),
        Theme(theme_id="T4", label="Narrow theme",
              assigned_studies=["S1", "S2"]),
    ]


def test_hasse_edges_connect_valid_themes(hierarchical_themes):
    """All Hasse edges must reference valid theme_ids."""
    result = analyse_partial_order(hierarchical_themes)
    valid_ids = {t.theme_id for t in hierarchical_themes}
    for edge in result["hasse_edges"]:
        assert edge["parent"] in valid_ids, f"Invalid parent: {edge['parent']}"
        assert edge["child"] in valid_ids, f"Invalid child: {edge['child']}"


def test_subsumption_relationship(hierarchical_themes):
    """T1 subsumes T2, T2 subsumes T4 — both should appear as comparable pairs."""
    result = analyse_partial_order(hierarchical_themes)
    # There should be at least some comparable pairs
    assert result["n_comparable_pairs"] > 0


def test_height_equals_longest_chain(hierarchical_themes):
    """Chain T1 > T2 > T4 has length 2, so height >= 2."""
    result = analyse_partial_order(hierarchical_themes)
    assert result["height"] >= 2


def test_moebius_self_values(hierarchical_themes):
    """mu(x, x) = 1 for all elements."""
    result = analyse_partial_order(hierarchical_themes)
    for t in hierarchical_themes:
        key = (t.theme_id, t.theme_id)
        assert result["moebius_values"].get(key) == 1, (
            f"mu({t.theme_id}, {t.theme_id}) should be 1"
        )


def test_zeta_z1_equals_element_count(hierarchical_themes):
    """Z(1) must equal the number of elements in the poset."""
    result = analyse_partial_order(hierarchical_themes)
    assert result["zeta_values"][1] == len(hierarchical_themes)
