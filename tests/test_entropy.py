import math
import pytest
from qualsynth.entropy import (
    shannon_entropy, normalized_entropy, gini_index,
    compute_saturation_curve,
)


def test_entropy_nonnegative():
    """Shannon entropy must be >= 0 for any distribution."""
    assert shannon_entropy([0, 0, 0]) == 0.0
    assert shannon_entropy([1]) == 0.0
    assert shannon_entropy([1, 1]) >= 0.0
    assert shannon_entropy([3, 2, 1]) >= 0.0


def test_entropy_uniform_is_log2k():
    """Uniform distribution of k categories gives H = log2(k)."""
    counts = [10, 10, 10, 10]
    h = shannon_entropy(counts)
    expected = math.log2(4)
    assert abs(h - expected) < 1e-10


def test_normalized_entropy_range():
    """Normalized entropy must be in [0, 1]."""
    assert normalized_entropy([5, 0]) >= 0.0
    assert normalized_entropy([5, 0]) <= 1.0
    assert normalized_entropy([5, 5]) <= 1.0 + 1e-12
    # Uniform -> normalized = 1.0
    assert abs(normalized_entropy([5, 5, 5]) - 1.0) < 1e-10


def test_saturation_curve_length(diabetes_studies, diabetes_themes):
    """Curve length must equal number of studies."""
    result = compute_saturation_curve(diabetes_studies, diabetes_themes)
    assert len(result["entropy_curve"]) == len(diabetes_studies)
    assert len(result["normalized_entropy_curve"]) == len(diabetes_studies)
    assert len(result["info_gain"]) == len(diabetes_studies)


def test_gini_range():
    """Gini index must be in [0, 1)."""
    assert gini_index([0]) == 0.0
    assert gini_index([1]) == 0.0
    g = gini_index([1, 1, 1, 1])
    assert 0.0 <= g < 1.0
    # Perfect concentration -> 0
    assert gini_index([10, 0, 0]) == 0.0
    # More spread -> higher Gini
    g2 = gini_index([5, 5, 5])
    assert g2 > 0.5
