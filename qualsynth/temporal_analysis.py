"""Temporal Evolution of Qualitative Evidence.

Pure Python implementation. Tracks how themes and findings evolve
across study publication years: emergence timelines, growth curves,
temporal diversity, innovation rate, paradigm shift detection,
influence graphs, and temporal co-evolution.
"""

import math


def _theme_studies_lookup(themes, studies):
    """Build dict mapping theme_id -> list of StudyInput objects assigned."""
    study_map = {s.study_id: s for s in studies}
    result = {}
    for theme in themes:
        assigned = []
        for sid in theme.assigned_studies:
            if sid in study_map:
                assigned.append(study_map[sid])
        result[theme.theme_id] = assigned
    return result


def compute_emergence_timeline(themes, studies):
    """For each theme, the earliest year a study in it was published.

    Returns:
        dict mapping theme_id -> int (year) or None if no studies
    """
    tsl = _theme_studies_lookup(themes, studies)
    result = {}
    for theme in themes:
        assigned = tsl.get(theme.theme_id, [])
        if assigned:
            result[theme.theme_id] = min(s.year for s in assigned)
        else:
            result[theme.theme_id] = None
    return result


def compute_growth_curves(themes, studies):
    """Cumulative count of studies per theme over time.

    Returns:
        dict mapping theme_id -> list of {"year": int, "cumulative": int}
    """
    tsl = _theme_studies_lookup(themes, studies)
    result = {}

    for theme in themes:
        assigned = tsl.get(theme.theme_id, [])
        if not assigned:
            result[theme.theme_id] = []
            continue

        years = sorted(s.year for s in assigned)
        min_year = years[0]
        max_year = years[-1]

        curve = []
        cumulative = 0
        year_counts = {}
        for y in years:
            year_counts[y] = year_counts.get(y, 0) + 1

        for y in range(min_year, max_year + 1):
            cumulative += year_counts.get(y, 0)
            curve.append({"year": y, "cumulative": cumulative})

        result[theme.theme_id] = curve

    return result


def _shannon_entropy(counts):
    """Shannon entropy H = -sum(p_i * log2(p_i))."""
    total = sum(counts)
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h


def compute_temporal_diversity(themes, studies):
    """Shannon entropy of theme distribution per year.

    Returns:
        list of {"year": int, "entropy": float}
    """
    if not studies:
        return []

    study_map = {s.study_id: s for s in studies}
    all_years = sorted(set(s.year for s in studies))

    result = []
    for year in all_years:
        # Count how many studies in this year belong to each theme
        year_study_ids = {s.study_id for s in studies if s.year == year}
        counts = []
        for theme in themes:
            assigned_in_year = len(
                set(theme.assigned_studies) & year_study_ids
            )
            counts.append(assigned_in_year)

        h = _shannon_entropy(counts)
        result.append({"year": year, "entropy": h})

    return result


def compute_innovation_rate(themes, studies):
    """Proportion of themes first appearing in each year / total themes.

    Returns:
        list of {"year": int, "rate": float}
    """
    emergence = compute_emergence_timeline(themes, studies)
    n_themes = len(themes)
    if n_themes == 0:
        return []

    # Count themes emerging per year
    year_count = {}
    for tid, year in emergence.items():
        if year is not None:
            year_count[year] = year_count.get(year, 0) + 1

    all_years = sorted(set(s.year for s in studies))
    result = []
    for year in all_years:
        count = year_count.get(year, 0)
        result.append({"year": year, "rate": count / n_themes})

    return result


def detect_paradigm_shifts(themes, studies):
    """Flag years where temporal diversity drops sharply (>30% decrease).

    Returns:
        list of years (ints)
    """
    td = compute_temporal_diversity(themes, studies)
    shifts = []

    for i in range(1, len(td)):
        prev = td[i - 1]["entropy"]
        curr = td[i]["entropy"]
        if prev > 0.0:
            drop = (prev - curr) / prev
            if drop > 0.30:
                shifts.append(td[i]["year"])

    return shifts


def build_influence_graph(themes, studies):
    """Build directed influence graph.

    If study A (year Y1) shares at least one theme with study B (year Y2 > Y1),
    add directed edge A -> B.

    Returns:
        edges: list of (study_id_from, study_id_to)
        influence_scores: dict study_id -> int (out-degree)
    """
    # Build study -> set of theme_ids
    study_themes = {}
    for theme in themes:
        for sid in theme.assigned_studies:
            if sid not in study_themes:
                study_themes[sid] = set()
            study_themes[sid].add(theme.theme_id)

    study_map = {s.study_id: s for s in studies}
    edges = []
    out_degree = {s.study_id: 0 for s in studies}

    for i, sa in enumerate(studies):
        for j, sb in enumerate(studies):
            if sa.year < sb.year:
                themes_a = study_themes.get(sa.study_id, set())
                themes_b = study_themes.get(sb.study_id, set())
                if themes_a & themes_b:
                    edges.append((sa.study_id, sb.study_id))
                    out_degree[sa.study_id] = out_degree.get(sa.study_id, 0) + 1

    return edges, out_degree


def compute_co_evolution(themes, studies):
    """Pearson correlation of cumulative study counts over time for each theme pair.

    Positive = co-evolving, negative = competing.

    Returns:
        dict mapping (theme_id_a, theme_id_b) -> float in [-1, 1]
    """
    if not studies:
        return {}

    growth = compute_growth_curves(themes, studies)

    # Build a common year range across all themes
    all_years = sorted(set(s.year for s in studies))
    if len(all_years) < 2:
        # Need at least 2 years for correlation
        result = {}
        for i, ta in enumerate(themes):
            for j, tb in enumerate(themes):
                if i < j:
                    result[(ta.theme_id, tb.theme_id)] = 0.0
        return result

    # Build cumulative vectors aligned to all_years
    def _aligned_cumulative(curve, all_years):
        """Align a growth curve to the common year range."""
        year_to_cum = {}
        for point in curve:
            year_to_cum[point["year"]] = point["cumulative"]

        vec = []
        last_cum = 0
        for y in all_years:
            if y in year_to_cum:
                last_cum = year_to_cum[y]
            vec.append(last_cum)
        return vec

    vectors = {}
    for theme in themes:
        curve = growth.get(theme.theme_id, [])
        vectors[theme.theme_id] = _aligned_cumulative(curve, all_years)

    def _pearson(x, y):
        """Pure Python Pearson correlation."""
        n = len(x)
        if n < 2:
            return 0.0
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        den_x = math.sqrt(sum((x[i] - mean_x) ** 2 for i in range(n)))
        den_y = math.sqrt(sum((y[i] - mean_y) ** 2 for i in range(n)))
        if den_x == 0.0 or den_y == 0.0:
            return 0.0
        return num / (den_x * den_y)

    result = {}
    for i, ta in enumerate(themes):
        for j, tb in enumerate(themes):
            if i < j:
                corr = _pearson(vectors[ta.theme_id], vectors[tb.theme_id])
                # Clamp to [-1, 1] for float precision
                corr = max(-1.0, min(1.0, corr))
                result[(ta.theme_id, tb.theme_id)] = corr

    return result


def analyse_temporal(studies, themes):
    """Full temporal evolution analysis.

    Returns:
        dict with keys:
            emergence_timeline: dict theme_id -> year
            growth_curves: dict theme_id -> list of {year, cumulative}
            temporal_diversity: list of {year, entropy}
            innovation_rate: list of {year, rate}
            paradigm_shifts: list of years
            influence_scores: dict study_id -> int
            co_evolution: dict (theme_id, theme_id) -> float
    """
    emergence = compute_emergence_timeline(themes, studies)
    growth = compute_growth_curves(themes, studies)
    td = compute_temporal_diversity(themes, studies)
    ir = compute_innovation_rate(themes, studies)
    shifts = detect_paradigm_shifts(themes, studies)
    edges, influence = build_influence_graph(themes, studies)
    coevo = compute_co_evolution(themes, studies)

    return {
        "emergence_timeline": emergence,
        "growth_curves": growth,
        "temporal_diversity": td,
        "innovation_rate": ir,
        "paradigm_shifts": shifts,
        "influence_scores": influence,
        "co_evolution": coevo,
    }
