"""Fuzzy Set Analysis of Theme Membership.

Pure Python implementation. Moves beyond binary theme assignment
to graded membership degrees, fuzzy set operations, fuzzy similarity,
fuzzy entropy, and defuzzification.
"""

import math
import re

from qualsynth.similarity import _tokenize


def _quality_weight(quality_score):
    """Map quality_score string to numeric weight."""
    mapping = {"high": 1.0, "moderate": 0.7, "low": 0.4}
    return mapping.get(quality_score, 0.5)


def _study_quote_ids(study):
    """Return set of quote_ids belonging to a study."""
    return {q.quote_id for q in study.quotes}


def _jaccard_tokens(text_a, text_b):
    """Jaccard similarity of tokenised texts."""
    tokens_a = set(_tokenize(text_a))
    tokens_b = set(_tokenize(text_b))
    if not tokens_a and not tokens_b:
        return 0.0
    inter = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(inter) / len(union) if union else 0.0


def compute_membership_matrix(studies, themes):
    """Compute fuzzy membership degree mu in [0,1] for each (study, theme) pair.

    Logic:
      - If the study has quotes and the theme has assigned_quotes,
        mu = (number of study's quotes assigned to theme) / (total quotes in study).
      - If no quotes match (or either side is empty), fall back to
        keyword overlap between study's key_findings and theme label (Jaccard of tokens).

    Returns:
        dict mapping (study_id, theme_id) -> float in [0, 1]
    """
    matrix = {}
    for study in studies:
        sq = _study_quote_ids(study)
        total_quotes = len(sq)
        findings_text = " ".join(study.key_findings)

        for theme in themes:
            tq = set(theme.assigned_quotes)

            if total_quotes > 0 and tq:
                overlap = sq & tq
                mu = len(overlap) / total_quotes
            else:
                # Fallback: Jaccard of tokens between key_findings and theme label + concepts
                theme_text = theme.label
                if theme.concepts:
                    theme_text += " " + " ".join(theme.concepts)
                mu = _jaccard_tokens(findings_text, theme_text)

            # Also consider assigned_studies as a binary signal
            if study.study_id in theme.assigned_studies:
                mu = max(mu, 0.5)  # at least 0.5 if explicitly assigned

            matrix[(study.study_id, theme.theme_id)] = mu

    return matrix


def compute_cardinalities(membership_matrix, themes):
    """Fuzzy cardinality per theme: sum of membership degrees.

    Returns:
        dict mapping theme_id -> float (effective number of studies)
    """
    result = {}
    for theme in themes:
        total = 0.0
        for (sid, tid), mu in membership_matrix.items():
            if tid == theme.theme_id:
                total += mu
        result[theme.theme_id] = total
    return result


def compute_core(membership_matrix, themes):
    """Core of each theme: studies with mu > 0.5.

    Returns:
        dict mapping theme_id -> list of study_ids
    """
    result = {}
    for theme in themes:
        core_studies = []
        for (sid, tid), mu in membership_matrix.items():
            if tid == theme.theme_id and mu > 0.5:
                core_studies.append(sid)
        result[theme.theme_id] = core_studies
    return result


def compute_support(membership_matrix, themes):
    """Support of each theme: studies with mu > 0.

    Returns:
        dict mapping theme_id -> list of study_ids
    """
    result = {}
    for theme in themes:
        support_studies = []
        for (sid, tid), mu in membership_matrix.items():
            if tid == theme.theme_id and mu > 0.0:
                support_studies.append(sid)
        result[theme.theme_id] = support_studies
    return result


def compute_alpha_cut(membership_matrix, themes, alpha=0.3):
    """Alpha-cut: studies with mu >= alpha.

    Returns:
        dict mapping theme_id -> list of study_ids
    """
    result = {}
    for theme in themes:
        cut_studies = []
        for (sid, tid), mu in membership_matrix.items():
            if tid == theme.theme_id and mu >= alpha:
                cut_studies.append(sid)
        result[theme.theme_id] = cut_studies
    return result


def fuzzy_jaccard(membership_matrix, studies, theme_a, theme_b):
    """Fuzzy Jaccard similarity between two themes.

    J = sum(min(mu_A, mu_B)) / sum(max(mu_A, mu_B))

    Returns:
        float in [0, 1]
    """
    num = 0.0
    den = 0.0
    for study in studies:
        mu_a = membership_matrix.get((study.study_id, theme_a.theme_id), 0.0)
        mu_b = membership_matrix.get((study.study_id, theme_b.theme_id), 0.0)
        num += min(mu_a, mu_b)
        den += max(mu_a, mu_b)
    if den == 0.0:
        return 0.0
    return num / den


def fuzzy_cosine(membership_matrix, studies, theme_a, theme_b):
    """Fuzzy cosine similarity between two themes.

    cos = sum(mu_A * mu_B) / (sqrt(sum(mu_A^2)) * sqrt(sum(mu_B^2)))

    Returns:
        float in [0, 1]
    """
    dot = 0.0
    mag_a = 0.0
    mag_b = 0.0
    for study in studies:
        mu_a = membership_matrix.get((study.study_id, theme_a.theme_id), 0.0)
        mu_b = membership_matrix.get((study.study_id, theme_b.theme_id), 0.0)
        dot += mu_a * mu_b
        mag_a += mu_a * mu_a
        mag_b += mu_b * mu_b
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (math.sqrt(mag_a) * math.sqrt(mag_b))


def compute_fuzzy_similarity(membership_matrix, studies, themes):
    """Compute fuzzy Jaccard similarity for all theme pairs.

    Returns:
        dict mapping (theme_id_a, theme_id_b) -> float
    """
    result = {}
    for i, ta in enumerate(themes):
        for j, tb in enumerate(themes):
            if i < j:
                sim = fuzzy_jaccard(membership_matrix, studies, ta, tb)
                result[(ta.theme_id, tb.theme_id)] = sim
    return result


def compute_fuzzy_entropy(membership_matrix, studies, themes):
    """Fuzzy entropy per theme.

    E = -1/(n*log(2)) * sum(mu*log(mu) + (1-mu)*log(1-mu))
    for mu not in {0, 1}.

    Higher entropy = more ambiguous theme boundaries.

    Returns:
        dict mapping theme_id -> float in [0, 1]
    """
    n = len(studies)
    result = {}
    for theme in themes:
        if n == 0:
            result[theme.theme_id] = 0.0
            continue

        entropy_sum = 0.0
        for study in studies:
            mu = membership_matrix.get((study.study_id, theme.theme_id), 0.0)
            if 0.0 < mu < 1.0:
                entropy_sum += mu * math.log(mu) + (1.0 - mu) * math.log(1.0 - mu)

        e = -entropy_sum / (n * math.log(2)) if n > 0 else 0.0
        # Clamp to [0, 1]
        e = max(0.0, min(1.0, e))
        result[theme.theme_id] = e
    return result


def compute_theme_sharpness(theme_entropy):
    """Theme sharpness = 1 - fuzzy_entropy.

    Higher sharpness = more clearly defined theme.

    Returns:
        dict mapping theme_id -> float in [0, 1]
    """
    return {tid: 1.0 - e for tid, e in theme_entropy.items()}


def compute_dominant_themes(membership_matrix, studies, themes):
    """For each study, the theme with highest membership degree.

    Returns:
        dict mapping study_id -> theme_id
    """
    result = {}
    for study in studies:
        best_theme = None
        best_mu = -1.0
        for theme in themes:
            mu = membership_matrix.get((study.study_id, theme.theme_id), 0.0)
            if mu > best_mu:
                best_mu = mu
                best_theme = theme.theme_id
        if best_theme is not None:
            result[study.study_id] = best_theme
    return result


def analyse_fuzzy_sets(studies, themes):
    """Full fuzzy set analysis.

    Returns:
        dict with keys:
            membership_matrix: dict (study_id, theme_id) -> float
            cardinalities: dict theme_id -> float
            fuzzy_similarity: dict (theme_id, theme_id) -> float
            theme_entropy: dict theme_id -> float
            theme_sharpness: dict theme_id -> float
            dominant_themes: dict study_id -> theme_id
    """
    mm = compute_membership_matrix(studies, themes)
    cardinalities = compute_cardinalities(mm, themes)
    fuzzy_sim = compute_fuzzy_similarity(mm, studies, themes)
    theme_ent = compute_fuzzy_entropy(mm, studies, themes)
    sharpness = compute_theme_sharpness(theme_ent)
    dominant = compute_dominant_themes(mm, studies, themes)

    return {
        "membership_matrix": mm,
        "cardinalities": cardinalities,
        "fuzzy_similarity": fuzzy_sim,
        "theme_entropy": theme_ent,
        "theme_sharpness": sharpness,
        "dominant_themes": dominant,
    }
