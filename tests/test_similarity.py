import pytest
from qualsynth.similarity import (
    compute_tfidf, cosine_similarity, build_similarity_matrix,
    suggest_theme_clusters, _tokenize,
)


def test_similarity_symmetric(diabetes_studies):
    """Similarity matrix must be symmetric: sim(i,j) == sim(j,i)."""
    matrix = build_similarity_matrix(diabetes_studies)
    n = len(diabetes_studies)
    for i in range(n):
        for j in range(n):
            assert abs(matrix[i][j] - matrix[j][i]) < 1e-12


def test_similarity_range(diabetes_studies):
    """All similarity values must be in [0, 1]."""
    matrix = build_similarity_matrix(diabetes_studies)
    for row in matrix:
        for val in row:
            assert 0.0 - 1e-12 <= val <= 1.0 + 1e-12


def test_self_similarity_is_one(diabetes_studies):
    """Diagonal entries (self-similarity) must be 1.0."""
    matrix = build_similarity_matrix(diabetes_studies)
    for i in range(len(diabetes_studies)):
        assert abs(matrix[i][i] - 1.0) < 1e-12


def test_suggest_clusters_returns_all_studies(diabetes_studies):
    """Every study must appear in exactly one cluster."""
    _, clusters, labels = suggest_theme_clusters(diabetes_studies, threshold=0.3)
    all_ids = set()
    for cluster in clusters:
        for sid in cluster:
            assert sid not in all_ids, f"{sid} appears in multiple clusters"
            all_ids.add(sid)
    expected = {s.study_id for s in diabetes_studies}
    assert all_ids == expected


def test_cluster_labels_nonempty(burnout_studies):
    """Each cluster should have at least one label term."""
    _, clusters, labels = suggest_theme_clusters(burnout_studies, threshold=0.3)
    assert len(labels) == len(clusters)
    for label_list in labels:
        assert len(label_list) >= 1
