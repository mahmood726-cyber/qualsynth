"""Automated reflexivity and methodological quality scoring.

Pure Python implementation. Computes 6 reflexivity indicators
measuring the rigor of the qualitative synthesis process, and
produces an overall score with traffic-light rating.
"""


def _theme_saturation(themes, n_studies):
    """Proportion of themes appearing in >50% of studies."""
    if not themes or n_studies <= 0:
        return 0.0
    threshold = n_studies / 2.0
    saturated = sum(1 for t in themes if len(t.assigned_studies) > threshold)
    return saturated / len(themes)


def _quote_density(themes):
    """Mean quotes per theme, normalized (cap at 1.0 for >=5)."""
    if not themes:
        return 0.0
    mean_quotes = sum(len(t.assigned_quotes) for t in themes) / len(themes)
    cap = 5.0
    return min(mean_quotes / cap, 1.0)


def _study_coverage(themes, studies):
    """Proportion of studies contributing to at least 1 theme."""
    if not studies:
        return 0.0
    all_ids = {s.study_id for s in studies}
    covered = set()
    for t in themes:
        covered.update(t.assigned_studies)
    covered = covered & all_ids
    return len(covered) / len(all_ids)


def _translation_completeness(translation_matrix):
    """Proportion of non-empty (non-absent) cells in translation matrix.

    If no matrix provided, returns 0.0.
    """
    if translation_matrix is None:
        return 0.0
    if not translation_matrix.cells:
        return 0.0
    non_empty = sum(1 for c in translation_matrix.cells if c.type != "absent")
    return non_empty / len(translation_matrix.cells)


def _disconfirming_evidence(themes):
    """Proportion of themes with at least one refutational concept.

    A concept is considered refutational if it contains 'refut' in
    its text (e.g., 'refutational', 'refutation'). This is a simple
    heuristic; in practice themes with concepts explicitly marked
    as refutational would be detected.
    """
    if not themes:
        return 0.0
    count = 0
    for t in themes:
        has_refutational = any("refut" in c.lower() for c in t.concepts)
        if has_refutational:
            count += 1
    return count / len(themes)


def _analytical_depth(themes):
    """Proportion of themes classified as 'analytical' vs 'descriptive'."""
    if not themes:
        return 0.0
    analytical = sum(1 for t in themes if t.level == "analytical")
    return analytical / len(themes)


def compute_reflexivity(studies, themes, translation_matrix=None):
    """Compute reflexivity indicators and overall score.

    Args:
        studies: list of StudyInput.
        themes: list of Theme with assigned_studies/assigned_quotes populated.
        translation_matrix: optional TranslationMatrix.

    Returns:
        dict with keys:
            indicators: dict of 6 indicator scores (each 0-1)
            overall_score: float (weighted mean, equal weights)
            rating: str ('Green', 'Amber', or 'Red')
            recommendations: list of str (for low-scoring indicators)
    """
    n_studies = len(studies)

    indicators = {
        "theme_saturation": _theme_saturation(themes, n_studies),
        "quote_density": _quote_density(themes),
        "study_coverage": _study_coverage(themes, studies),
        "translation_completeness": _translation_completeness(translation_matrix),
        "disconfirming_evidence": _disconfirming_evidence(themes),
        "analytical_depth": _analytical_depth(themes),
    }

    # Overall score: equal-weighted mean
    values = list(indicators.values())
    overall = sum(values) / len(values) if values else 0.0

    # Traffic light
    if overall >= 0.7:
        rating = "Green"
    elif overall >= 0.4:
        rating = "Amber"
    else:
        rating = "Red"

    # Recommendations for low-scoring indicators
    recommendations = []
    threshold = 0.5
    label_map = {
        "theme_saturation": "Consider whether themes are sufficiently grounded across studies; some themes appear in few studies.",
        "quote_density": "Increase the number of supporting quotes per theme to strengthen evidence base.",
        "study_coverage": "Some studies do not contribute to any theme; review for missed findings.",
        "translation_completeness": "Translation matrix has many empty cells; consider whether concepts are too narrowly defined.",
        "disconfirming_evidence": "No refutational or disconfirming concepts found; actively seek contradictory evidence.",
        "analytical_depth": "Most themes are descriptive; develop higher-order analytical themes.",
    }
    for key, score in indicators.items():
        if score < threshold:
            recommendations.append(label_map[key])

    return {
        "indicators": indicators,
        "overall_score": overall,
        "rating": rating,
        "recommendations": recommendations,
    }
