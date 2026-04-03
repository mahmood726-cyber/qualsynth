"""Information-theoretic saturation analysis for qualitative synthesis.

Pure Python implementation (no numpy/scipy). Uses Shannon entropy
to measure when adding more studies stops yielding new thematic
information.
"""

import math


def _theme_distribution(themes, study_ids):
    """Count quotes per theme for the given set of study_ids.

    Returns a list of counts (one per theme, in order).
    """
    counts = []
    for t in themes:
        n = 0
        for qid in t.assigned_quotes:
            # A quote contributes if its study is in the included set.
            # Since quotes don't carry study_id directly, we count by
            # how many assigned_studies overlap with included study_ids.
            pass
        # Use study-level contribution: count how many of the theme's
        # assigned studies are in the included set.
        n = sum(1 for sid in t.assigned_studies if sid in study_ids)
        counts.append(n)
    return counts


def shannon_entropy(counts):
    """Shannon entropy H = -sum(p_i * log2(p_i)).

    Args:
        counts: list of non-negative integers (theme frequencies).

    Returns:
        H >= 0.  Returns 0.0 if all counts are zero.
    """
    total = sum(counts)
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h


def normalized_entropy(counts):
    """Normalized entropy H / log2(k), in [0, 1].

    k = number of categories with any possibility (length of counts).
    Returns 0.0 if k <= 1.
    """
    k = len(counts)
    if k <= 1:
        return 0.0
    h = shannon_entropy(counts)
    h_max = math.log2(k)
    if h_max == 0.0:
        return 0.0
    return h / h_max


def gini_index(counts):
    """Gini index of concentration: 1 - sum(p_i^2).

    Returns 0.0 for perfect concentration, approaches 1 for uniform.
    """
    total = sum(counts)
    if total == 0:
        return 0.0
    return 1.0 - sum((c / total) ** 2 for c in counts)


def compute_saturation_curve(studies, themes, threshold=0.05):
    """Compute entropy-based saturation curve.

    Studies are added in the order provided. For each cumulative set,
    we compute theme distribution, entropy, and information gain.

    Args:
        studies: list of StudyInput (order matters).
        themes: list of Theme with assigned_studies populated.
        threshold: information gain below which saturation is reached.

    Returns:
        dict with keys:
            entropy_curve: list of floats (H for 1..n studies)
            normalized_entropy_curve: list of floats
            info_gain: list of floats (delta H; first entry is H(1))
            saturation_index: int or None (first index where gain < threshold)
            mutual_information: float I(S;T)
            gini_index: float (for full dataset)
    """
    n = len(studies)
    entropy_curve = []
    norm_curve = []
    info_gain = []
    saturation_index = None

    for i in range(1, n + 1):
        included = {s.study_id for s in studies[:i]}
        counts = _theme_distribution(themes, included)
        h = shannon_entropy(counts)
        nh = normalized_entropy(counts)
        entropy_curve.append(h)
        norm_curve.append(nh)

        if i == 1:
            info_gain.append(h)
        else:
            delta = h - entropy_curve[i - 2]
            info_gain.append(delta)

        if saturation_index is None and i > 1:
            if abs(info_gain[-1]) < threshold:
                saturation_index = i - 1  # 0-based index of the study

    # Mutual information: I(S;T) = H(T) - H(T|S)
    # H(T) = entropy of theme distribution across all studies
    all_ids = {s.study_id for s in studies}
    full_counts = _theme_distribution(themes, all_ids)
    h_t = shannon_entropy(full_counts)

    # H(T|S) = weighted average of H(T | study = s_i)
    h_t_given_s = 0.0
    total_contribution = sum(full_counts)
    if total_contribution > 0 and n > 0:
        for s in studies:
            sid_set = {s.study_id}
            s_counts = _theme_distribution(themes, sid_set)
            s_total = sum(s_counts)
            if s_total > 0:
                weight = s_total / total_contribution
                h_t_given_s += weight * shannon_entropy(s_counts)

    mi = h_t - h_t_given_s

    gi = gini_index(full_counts)

    return {
        "entropy_curve": entropy_curve,
        "normalized_entropy_curve": norm_curve,
        "info_gain": info_gain,
        "saturation_index": saturation_index,
        "mutual_information": mi,
        "gini_index": gi,
    }
