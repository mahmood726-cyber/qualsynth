"""Bayesian Theme Richness Estimation (ecological species-richness model).

Pure Python implementation — estimates total theme population (including
unseen themes) using Chao1, Good-Turing, rarefaction, and extrapolation.
Uses only the math module.
"""

import math


# ---------- helpers ----------

def _log_comb(n, k):
    """Log of binomial coefficient C(n, k) in a numerically safe way.

    Uses log-space summation:  log C(n,k) = sum_{i=1}^{k} log(n-i+1) - log(i)
    Returns -inf if k > n or k < 0.
    """
    if k < 0 or k > n:
        return float("-inf")
    if k == 0 or k == n:
        return 0.0
    # Use the smaller of k and n-k for efficiency
    k = min(k, n - k)
    result = 0.0
    for i in range(1, k + 1):
        result += math.log(n - i + 1) - math.log(i)
    return result


def _frequency_counts(themes, study_ids_list):
    """Count how many studies each theme appears in.

    Args:
        themes: list of Theme (with assigned_studies populated).
        study_ids_list: list of study_id strings (the study pool).

    Returns:
        abundances: list of ints (count per theme, only themes with count > 0)
        f_counts: dict {count: number_of_themes_with_that_count}
        n_total: total number of theme-study assignments
    """
    pool = set(study_ids_list)
    abundances = []
    for t in themes:
        n = sum(1 for sid in t.assigned_studies if sid in pool)
        if n > 0:
            abundances.append(n)

    f_counts = {}
    for a in abundances:
        f_counts[a] = f_counts.get(a, 0) + 1

    n_total = sum(abundances)
    return abundances, f_counts, n_total


# ---------- Chao1 ----------

def _chao1(s_obs, f1, f2):
    """Chao1 estimator for total richness.

    S_est = S_obs + f1^2 / (2*f2)       if f2 > 0
    S_est = S_obs + f1*(f1-1) / 2        if f2 == 0
    """
    if f2 > 0:
        return s_obs + (f1 * f1) / (2.0 * f2)
    else:
        return s_obs + f1 * (f1 - 1) / 2.0


def _chao1_ci(s_obs, f1, f2, z=1.96):
    """Log-transformed confidence interval for Chao1.

    CI: S_obs + (S_est - S_obs) * exp(±z * se_log)
    where se_log is on the log scale of (S_est - S_obs).
    """
    s_est = _chao1(s_obs, f1, f2)
    d = s_est - s_obs  # estimated unseen

    if d <= 0:
        return (s_obs, s_obs)

    # Variance of the unseen portion
    if f2 > 0:
        var_d = (f1 ** 2 / (2 * f2)) * (
            1.0 + (f1 ** 2) / (4.0 * f2 ** 2)
        )
    else:
        var_d = f1 * (f1 - 1) / 2.0 + f1 * (2 * f1 - 1) ** 2 / 4.0

    if var_d <= 0 or d <= 0:
        return (s_obs, s_est)

    # Log-normal CI
    C = math.exp(z * math.sqrt(math.log(1.0 + var_d / (d * d))))
    lo = s_obs + d / C
    hi = s_obs + d * C
    return (lo, hi)


# ---------- Good-Turing ----------

def _good_turing_p_new(f1, n_total):
    """Probability of discovering a new theme in the next study.

    P(new) = f1 / N_total
    """
    if n_total <= 0:
        return 0.0
    return f1 / n_total


# ---------- Rarefaction ----------

def _rarefaction_expected(abundances, m, N):
    """Expected number of themes in a subsample of m studies.

    E[S(m)] = S_obs - sum_j C(N - n_j, m) / C(N, m)

    Uses log-space for numerical stability.
    """
    s_obs = len(abundances)
    log_c_N_m = _log_comb(N, m)

    reduction = 0.0
    for n_j in abundances:
        if N - n_j >= m:
            log_term = _log_comb(N - n_j, m) - log_c_N_m
            reduction += math.exp(log_term)
        # else: C(N-n_j, m) = 0 when N-n_j < m (theme must be present)

    return s_obs - reduction


# ---------- Extrapolation ----------

def _extrapolation_expected(s_obs, f1, n_total, m):
    """Predicted number of themes at m > n studies using Chao1.

    S(m) = S_est - (S_est - S_obs) * exp(-f1 * (m - N) / (S_est - S_obs))
    where S_est is the Chao1 estimate and N is the current total.
    """
    # f2 is not directly available here; use f1 only estimate
    s_est = s_obs + f1 * (f1 - 1) / 2.0 if f1 > 1 else s_obs + f1
    d = s_est - s_obs
    if d <= 0 or f1 <= 0:
        return s_obs

    extra = m - n_total
    if extra <= 0:
        return s_obs

    return s_est - d * math.exp(-f1 * extra / d)


# ---------- Public API ----------

def estimate_theme_richness(themes, studies):
    """Estimate total theme richness using ecological models.

    Args:
        themes: list of Theme (with assigned_studies populated).
        studies: list of StudyInput (defines the study pool).

    Returns:
        dict with keys:
            chao1_estimate: float (estimated total themes including unseen)
            chao1_ci: tuple (lower, upper) 95% CI
            good_turing_p_new: float (prob of new theme in next study)
            rarefaction_curve: list of {m, expected_themes}
            extrapolation_curve: list of {m, expected_themes}
            coverage: float (Good-Turing sample coverage)
            unseen_estimate: float (estimated number of unseen themes)
    """
    study_ids = [s.study_id for s in studies]
    n_studies = len(study_ids)

    abundances, f_counts, n_total = _frequency_counts(themes, study_ids)
    s_obs = len(abundances)  # number of observed themes (with >=1 study)

    f1 = f_counts.get(1, 0)  # singletons
    f2 = f_counts.get(2, 0)  # doubletons

    # Chao1
    chao1_est = _chao1(s_obs, f1, f2)
    chao1_ci = _chao1_ci(s_obs, f1, f2)

    # Good-Turing
    gt_p_new = _good_turing_p_new(f1, n_total)

    # Coverage
    coverage = 1.0 - gt_p_new if n_total > 0 else 0.0

    # Rarefaction curve: m = 1 .. n_studies
    rarefaction = []
    for m in range(1, n_studies + 1):
        expected = _rarefaction_expected(abundances, m, n_studies)
        rarefaction.append({"m": m, "expected_themes": expected})

    # Extrapolation curve: m = n_studies+1 .. 2*n_studies
    extrapolation = []
    max_m = max(n_studies * 2, n_studies + 5)
    for m in range(n_studies + 1, max_m + 1):
        expected = _extrapolation_expected(s_obs, f1, n_studies, m)
        extrapolation.append({"m": m, "expected_themes": expected})

    unseen = max(0.0, chao1_est - s_obs)

    return {
        "chao1_estimate": chao1_est,
        "chao1_ci": chao1_ci,
        "good_turing_p_new": gt_p_new,
        "rarefaction_curve": rarefaction,
        "extrapolation_curve": extrapolation,
        "coverage": coverage,
        "unseen_estimate": unseen,
    }
