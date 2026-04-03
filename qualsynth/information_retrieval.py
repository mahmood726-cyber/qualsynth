"""Information Retrieval Metrics for Theme Quality.

Pure Python implementation. Treats theme assignment as a retrieval
task and measures precision, recall, F1, MAP, NDCG, and AUC-ROC
for each theme.
"""

import math


def _quality_weight(quality_score):
    """Map quality_score string to numeric weight."""
    mapping = {"high": 1.0, "moderate": 0.7, "low": 0.4}
    return mapping.get(quality_score, 0.5)


def _study_lookup(studies):
    """Build dict from study_id to StudyInput."""
    return {s.study_id: s for s in studies}


def compute_precision(themes, studies):
    """Precision per theme.

    Proxy: mean quality_weight of assigned studies.
    quality_weight: high=1.0, moderate=0.7, low=0.4.

    Returns:
        dict mapping theme_id -> float in [0, 1]
    """
    lookup = _study_lookup(studies)
    result = {}
    for theme in themes:
        assigned = [sid for sid in theme.assigned_studies if sid in lookup]
        if not assigned:
            result[theme.theme_id] = 0.0
            continue
        weights = [_quality_weight(lookup[sid].quality_score) for sid in assigned]
        result[theme.theme_id] = sum(weights) / len(weights)
    return result


def compute_recall(themes, studies):
    """Recall per theme (theme saturation).

    Proxy: proportion of all studies that contribute to this theme.

    Returns:
        dict mapping theme_id -> float in [0, 1]
    """
    n = len(studies)
    result = {}
    for theme in themes:
        if n == 0:
            result[theme.theme_id] = 0.0
            continue
        n_assigned = len(theme.assigned_studies)
        result[theme.theme_id] = min(n_assigned / n, 1.0)
    return result


def compute_f1(precision, recall):
    """F1 score per theme: 2*P*R / (P+R).

    Returns:
        dict mapping theme_id -> float in [0, 1]
    """
    result = {}
    for tid in precision:
        p = precision[tid]
        r = recall.get(tid, 0.0)
        if p + r == 0.0:
            result[tid] = 0.0
        else:
            result[tid] = 2.0 * p * r / (p + r)
    return result


def compute_map_score(precision):
    """Mean Average Precision: average precision across all themes.

    Returns:
        float in [0, 1]
    """
    if not precision:
        return 0.0
    return sum(precision.values()) / len(precision)


def compute_ndcg(themes, studies, membership_matrix=None):
    """NDCG (Normalized Discounted Cumulative Gain) per theme.

    Ranks studies within each theme by membership strength
    (or by position in assigned_studies if no membership_matrix).
    relevance = quality_weight of study.

    DCG = sum(relevance_i / log2(i+1)) for i=1..n
    NDCG = DCG / ideal_DCG

    Returns:
        dict mapping theme_id -> float in [0, 1]
    """
    lookup = _study_lookup(studies)
    result = {}

    for theme in themes:
        assigned = [sid for sid in theme.assigned_studies if sid in lookup]
        if not assigned:
            result[theme.theme_id] = 0.0
            continue

        # Get relevance scores
        relevances = []
        for sid in assigned:
            rel = _quality_weight(lookup[sid].quality_score)
            if membership_matrix is not None:
                mu = membership_matrix.get((sid, theme.theme_id), 0.0)
            else:
                mu = 1.0
            relevances.append((mu, rel, sid))

        # Sort by membership strength (descending) for actual ranking
        relevances.sort(key=lambda x: -x[0])
        actual_rels = [r[1] for r in relevances]

        # Compute DCG
        dcg = 0.0
        for i, rel in enumerate(actual_rels):
            dcg += rel / math.log2(i + 2)  # i+2 because i is 0-based

        # Ideal DCG: sort relevances descending
        ideal_rels = sorted(actual_rels, reverse=True)
        idcg = 0.0
        for i, rel in enumerate(ideal_rels):
            idcg += rel / math.log2(i + 2)

        if idcg == 0.0:
            result[theme.theme_id] = 0.0
        else:
            result[theme.theme_id] = dcg / idcg

    return result


def compute_auc_roc(themes, studies, membership_matrix):
    """AUC-ROC per theme using Mann-Whitney U statistic.

    For each theme, use fuzzy membership as score and binary
    assignment (study in assigned_studies) as label.
    AUC = count concordant pairs / total pairs.

    Returns:
        dict mapping theme_id -> float in [0, 1]
    """
    result = {}

    for theme in themes:
        assigned_set = set(theme.assigned_studies)
        positives = []
        negatives = []

        for study in studies:
            mu = membership_matrix.get((study.study_id, theme.theme_id), 0.0)
            if study.study_id in assigned_set:
                positives.append(mu)
            else:
                negatives.append(mu)

        if not positives or not negatives:
            # AUC undefined when only one class; default to 0.5
            result[theme.theme_id] = 0.5
            continue

        # Mann-Whitney U
        concordant = 0
        tied = 0
        total = len(positives) * len(negatives)
        for p in positives:
            for n in negatives:
                if p > n:
                    concordant += 1
                elif p == n:
                    tied += 1

        auc = (concordant + 0.5 * tied) / total if total > 0 else 0.5
        result[theme.theme_id] = auc

    return result


def analyse_information_retrieval(studies, themes, membership_matrix=None):
    """Full information retrieval analysis.

    Args:
        studies: list of StudyInput
        themes: list of Theme (with assigned_studies populated)
        membership_matrix: optional dict (study_id, theme_id) -> float
            from fuzzy_sets module. If None, AUC defaults to 0.5.

    Returns:
        dict with keys:
            precision: dict theme_id -> float
            recall: dict theme_id -> float
            f1: dict theme_id -> float
            map_score: float
            ndcg: dict theme_id -> float
            auc_roc: dict theme_id -> float
            mean_auc: float
    """
    prec = compute_precision(themes, studies)
    rec = compute_recall(themes, studies)
    f1 = compute_f1(prec, rec)
    map_score = compute_map_score(prec)
    ndcg = compute_ndcg(themes, studies, membership_matrix)

    if membership_matrix is not None:
        auc = compute_auc_roc(themes, studies, membership_matrix)
    else:
        auc = {t.theme_id: 0.5 for t in themes}

    mean_auc = sum(auc.values()) / len(auc) if auc else 0.5

    return {
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "map_score": map_score,
        "ndcg": ndcg,
        "auc_roc": auc,
        "mean_auc": mean_auc,
    }
