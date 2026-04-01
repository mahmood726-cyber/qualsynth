import pytest
from qualsynth.translation import build_translation_matrix, compute_coverage, compute_consistency, classify_translation


def test_build_matrix(burnout_studies, burnout_data):
    concepts = burnout_data[3].get("concepts", [])
    matrix = build_translation_matrix(burnout_studies, concepts)
    assert len(matrix.concepts) == len(concepts)
    assert len(matrix.studies) == len(burnout_studies)


def test_coverage_all_present():
    coverage = compute_coverage(n_present=5, n_studies=5)
    assert coverage == 1.0


def test_coverage_partial():
    coverage = compute_coverage(n_present=3, n_studies=5)
    assert abs(coverage - 0.6) < 0.01


def test_consistency_all_reciprocal():
    consistency = compute_consistency(n_present=5, n_refutational=0)
    assert consistency == 1.0


def test_classify_reciprocal():
    assert classify_translation(consistency=0.9, has_refutational=False) == "reciprocal"


def test_classify_refutational():
    assert classify_translation(consistency=0.4, has_refutational=True) == "refutational"


def test_classify_line_of_argument():
    assert classify_translation(consistency=0.7, has_refutational=True) == "line_of_argument"
