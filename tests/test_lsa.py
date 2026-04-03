import pytest
from qualsynth.lsa import run_lsa


def test_lsa_n_concepts_bounded(diabetes_studies):
    """Number of extracted concepts must be <= n_studies - 1."""
    result = run_lsa(diabetes_studies)
    n = len(diabetes_studies)
    assert result["n_concepts"] <= n - 1
    assert result["n_concepts"] >= 1
    assert len(result["concepts"]) == result["n_concepts"]


def test_lsa_similarity_matrix_shape(diabetes_studies):
    """Semantic similarity matrix must be n_studies x n_studies."""
    result = run_lsa(diabetes_studies)
    n = len(diabetes_studies)
    assert len(result["semantic_similarity_matrix"]) == n
    for row in result["semantic_similarity_matrix"]:
        assert len(row) == n


def test_lsa_similarity_range(diabetes_studies):
    """All similarity values must be in [0, 1]."""
    result = run_lsa(diabetes_studies)
    for row in result["semantic_similarity_matrix"]:
        for val in row:
            assert -1e-9 <= val <= 1.0 + 1e-9, f"Similarity {val} out of range"


def test_lsa_variance_explained_range(burnout_studies):
    """Total variance explained must be in [0, 1], each concept <= 1."""
    result = run_lsa(burnout_studies)
    assert 0.0 <= result["total_variance_explained"] <= 1.0 + 1e-9
    for concept in result["concepts"]:
        assert 0.0 <= concept["variance_explained"] <= 1.0 + 1e-9


def test_lsa_concept_top_terms(diabetes_studies):
    """Each concept must have between 1 and 5 top terms."""
    result = run_lsa(diabetes_studies)
    for concept in result["concepts"]:
        assert 1 <= len(concept["top_terms"]) <= 5
        # All terms should be non-empty strings
        for term in concept["top_terms"]:
            assert isinstance(term, str)
            assert len(term) > 0
