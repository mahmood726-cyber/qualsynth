import pytest
from qualsynth.embeddings import compute_word_embeddings


def test_word_vectors_correct_dimensions(diabetes_studies):
    """Word vectors must have the declared embedding_dim dimensions."""
    result = compute_word_embeddings(diabetes_studies, embedding_dim=5)
    dim = result["embedding_dim"]
    assert dim > 0
    for word, vec in result["word_vectors"].items():
        assert len(vec) == dim, f"Word '{word}' has {len(vec)} dims, expected {dim}"


def test_vocabulary_non_empty(diabetes_studies):
    """Vocabulary must be non-empty for a real dataset."""
    result = compute_word_embeddings(diabetes_studies)
    assert len(result["vocabulary"]) > 0
    # Every word in vocabulary should have a vector
    for w in result["vocabulary"]:
        assert w in result["word_vectors"]


def test_nearest_neighbors_structure(diabetes_studies):
    """Each word should have up to 5 nearest neighbors (all different from query)."""
    result = compute_word_embeddings(diabetes_studies)
    for word, neighbors in result["nearest_neighbors"].items():
        assert len(neighbors) <= 5
        assert word not in neighbors, f"Word '{word}' is its own neighbor"
        # All neighbors must be in vocabulary
        for n in neighbors:
            assert n in result["word_vectors"]


def test_concept_clusters_cover_vocabulary(diabetes_studies):
    """Concept clusters must collectively contain all vocabulary words."""
    result = compute_word_embeddings(diabetes_studies)
    all_words = set()
    for cluster in result["concept_clusters"]:
        for w in cluster:
            all_words.add(w)
    vocab_set = set(result["vocabulary"])
    assert all_words == vocab_set, "Clusters must cover entire vocabulary"


def test_burnout_embeddings(burnout_studies):
    """Embeddings work on a different dataset; vectors are finite floats."""
    result = compute_word_embeddings(burnout_studies, embedding_dim=3)
    assert result["embedding_dim"] >= 1
    for word, vec in result["word_vectors"].items():
        for val in vec:
            assert isinstance(val, float)
            assert val == val, f"NaN in vector for '{word}'"  # NaN check
