"""Tests for topic_model.py — simplified LDA via collapsed Gibbs sampling."""

import pytest
from qualsynth.topic_model import run_lda


def test_topic_proportions_sum_to_one(diabetes_studies):
    """Per-study topic proportions must sum to approximately 1.0."""
    result = run_lda(diabetes_studies, n_topics=3, n_iter=50, seed=42)
    for sid, props in result["study_topic_proportions"].items():
        total = sum(props)
        assert abs(total - 1.0) < 1e-6, (
            f"Proportions for {sid} sum to {total}, expected ~1.0"
        )


def test_correct_number_of_topics(diabetes_studies):
    """Number of topics returned must match n_topics parameter."""
    for k in (2, 3, 4):
        result = run_lda(diabetes_studies, n_topics=k, n_iter=30, seed=123)
        assert len(result["topics"]) == k
        assert result["n_topics"] == k


def test_perplexity_is_finite(diabetes_studies):
    """Perplexity should be a positive finite number for real data."""
    result = run_lda(diabetes_studies, n_topics=3, n_iter=50, seed=42)
    assert result["perplexity"] > 0
    assert result["perplexity"] < float("inf")


def test_coherence_scores_per_topic(diabetes_studies):
    """One coherence score per topic."""
    result = run_lda(diabetes_studies, n_topics=3, n_iter=50, seed=42)
    assert len(result["coherence_scores"]) == 3


def test_deterministic_with_seed(diabetes_studies):
    """Same seed must produce identical results."""
    r1 = run_lda(diabetes_studies, n_topics=2, n_iter=40, seed=99)
    r2 = run_lda(diabetes_studies, n_topics=2, n_iter=40, seed=99)
    assert r1["study_topic_proportions"] == r2["study_topic_proportions"]
    assert r1["perplexity"] == r2["perplexity"]
