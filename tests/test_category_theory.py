import pytest
from qualsynth.models import Theme
from qualsynth.category_theory import analyse_category


@pytest.fixture
def category_themes():
    """Themes with subset/superset study relationships for category analysis."""
    return [
        Theme(theme_id="T1", label="Narrow theme",
              assigned_studies=["S1", "S2"]),
        Theme(theme_id="T2", label="Medium theme",
              assigned_studies=["S1", "S2", "S3"]),
        Theme(theme_id="T3", label="Broad theme",
              assigned_studies=["S1", "S2", "S3", "S4", "S5"]),
        Theme(theme_id="T4", label="Disjoint theme",
              assigned_studies=["S6"]),
        Theme(theme_id="T5", label="Duplicate of narrow",
              assigned_studies=["S1", "S2"]),
    ]


def test_morphisms_include_identities(category_themes):
    """Every theme must have an identity morphism (T -> T)."""
    result = analyse_category(category_themes)
    morphisms = result["morphisms"]
    for t in category_themes:
        assert (t.theme_id, t.theme_id) in morphisms, (
            f"Missing identity morphism for {t.theme_id}"
        )


def test_morphisms_subsumption(category_themes):
    """T1 (S1,S2) should have morphism to T2 (S1,S2,S3) since T1 subset T2."""
    result = analyse_category(category_themes)
    morphisms = result["morphisms"]
    # T1 subset T2 subset T3
    assert ("T1", "T2") in morphisms
    assert ("T1", "T3") in morphisms
    assert ("T2", "T3") in morphisms
    # T3 is NOT a subset of T1
    assert ("T3", "T1") not in morphisms


def test_products_intersection(category_themes):
    """Product of T1 and T2 should be their intersection {S1, S2}."""
    result = analyse_category(category_themes)
    products = result["products"]
    key = ("T1", "T2")
    assert key in products, "Missing product for T1 x T2"
    assert products[key] == {"S1", "S2"}


def test_isomorphism_classes(category_themes):
    """T1 and T5 have identical study sets, so n_iso_classes < n_themes."""
    result = analyse_category(category_themes)
    # T1 and T5 share {S1, S2}, so they form one iso class
    assert result["n_iso_classes"] == len(category_themes) - 1


def test_adjunction_score_range(category_themes):
    """Adjunction score must be in [0, 1]."""
    result = analyse_category(category_themes)
    score = result["adjunction_score"]
    assert 0.0 <= score <= 1.0, f"Adjunction score {score} out of range"
    # All themes have assigned studies, so round-trip should recover them
    assert score > 0.0, "Expected positive adjunction score"
