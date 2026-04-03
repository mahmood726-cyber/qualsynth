"""Hermeneutic Circle Formalization — Conceptual Depth Analysis.

Measures interpretive depth and theoretical development of
qualitative themes using abstraction ladders, coding density,
and a composite hermeneutic depth index.

Pure Python implementation (no numpy/scipy).
"""


# ---------- Abstraction level indicators ----------

LEVEL_1_DESCRIPTIVE = frozenset([
    "experience", "experiences", "experiencing",
    "feeling", "feelings",
    "barrier", "barriers",
    "challenge", "challenges",
    "practice", "practices",
    "behavior", "behaviour", "behaviors", "behaviours",
    "need", "needs",
    "concern", "concerns",
    "problem", "problems",
    "difficulty", "difficulties",
    "burden", "impact",
    "struggle", "struggles",
    "support", "coping",
    "daily", "routine",
    "symptom", "symptoms",
    "stress", "fear",
    "management", "self-management",
    "identity", "disruption",
    "navigation", "knowledge",
    "fatigue", "tension",
])

LEVEL_2_INTERPRETIVE = frozenset([
    "perception", "perceptions",
    "meaning", "meanings",
    "understanding", "understandings",
    "belief", "beliefs",
    "attitude", "attitudes",
    "perspective", "perspectives",
    "interpretation", "interpretations",
    "sense-making", "sensemaking",
    "awareness", "insight",
    "value", "values",
    "expectation", "expectations",
    "motivation", "motivations",
    "view", "views",
    "appraisal",
    "significance",
    "lived",
    "contested",
    "empowerment",
])

LEVEL_3_EXPLANATORY = frozenset([
    "mechanism", "mechanisms",
    "process", "processes",
    "pathway", "pathways",
    "dynamic", "dynamics",
    "interaction", "interactions",
    "relationship", "relationships",
    "influence", "influences",
    "mediation", "moderation",
    "causation", "causal",
    "trajectory", "trajectories",
    "transition", "transitions",
    "adaptation", "transformation",
    "negotiation", "reconciliation",
    "cycle", "feedback",
])

LEVEL_4_THEORETICAL = frozenset([
    "framework", "frameworks",
    "model", "models",
    "theory", "theories",
    "paradigm", "paradigms",
    "construct", "constructs",
    "dimension", "dimensions",
    "typology", "taxonomy",
    "ontology", "epistemology",
    "phenomenology", "hermeneutic",
    "dialectic", "praxis",
    "schema", "archetype",
])


# ---------- Abstraction level classification ----------

def _classify_abstraction_level(theme):
    """Classify a theme's abstraction level (1-4).

    Uses theme label word matching against indicator lists,
    falling back to the theme's `level` field.
    """
    label_lower = theme.label.lower()
    words = set(
        w.strip(".,;:!?\"'()-")
        for w in label_lower.split()
    )

    # Check from highest to lowest (prefer highest match)
    if words & LEVEL_4_THEORETICAL:
        return 4
    if words & LEVEL_3_EXPLANATORY:
        return 3
    if words & LEVEL_2_INTERPRETIVE:
        return 2
    if words & LEVEL_1_DESCRIPTIVE:
        return 1

    # Fall back to theme.level field
    level_map = {
        "descriptive": 1,
        "interpretive": 2,
        "analytical": 3,
    }
    return level_map.get(theme.level, 1)


# ---------- Coding density ----------

def _compute_coding_density(studies, themes):
    """Compute coding density: unique codes per study / key_findings count.

    Density = mean across studies of (n_quotes_assigned / max(1, n_key_findings)).
    """
    if not studies:
        return 0.0

    # Build map: study_id -> set of quotes assigned to any theme
    study_quotes = {}
    for theme in themes:
        for qid in theme.assigned_quotes:
            for s in studies:
                for q in s.quotes:
                    if q.quote_id == qid:
                        if s.study_id not in study_quotes:
                            study_quotes[s.study_id] = set()
                        study_quotes[s.study_id].add(qid)

    densities = []
    for s in studies:
        n_findings = max(1, len(s.key_findings))
        n_codes = len(study_quotes.get(s.study_id, set()))
        densities.append(n_codes / n_findings)

    if not densities:
        return 0.0
    return sum(densities) / len(densities)


# ---------- Theme hierarchy depth ----------

def _max_hierarchy_depth(themes):
    """Compute max parent chain length in theme hierarchy."""
    theme_map = {t.theme_id: t for t in themes}
    max_depth = 0

    for theme in themes:
        depth = 0
        current = theme
        visited = set()
        while current.parent_id and current.parent_id in theme_map:
            if current.parent_id in visited:
                break  # Avoid cycles
            visited.add(current.parent_id)
            depth += 1
            current = theme_map[current.parent_id]
        if depth > max_depth:
            max_depth = depth

    return max_depth


# ---------- Cross-study concept recurrence ----------

def _concept_recurrence(themes, studies):
    """Mean concept frequency across studies.

    For each concept in themes, count how many studies it appears in
    (via assigned_studies of themes containing that concept).
    Return mean frequency normalized by total studies.
    """
    if not studies or not themes:
        return 0.0

    n_studies = len(studies)
    concept_study_count = {}

    for theme in themes:
        for concept in theme.concepts:
            if concept not in concept_study_count:
                concept_study_count[concept] = set()
            concept_study_count[concept].update(theme.assigned_studies)

    if not concept_study_count:
        # If no explicit concepts, use themes themselves as concepts
        for theme in themes:
            concept_study_count[theme.theme_id] = set(theme.assigned_studies)

    if not concept_study_count:
        return 0.0

    freqs = [len(sids) / n_studies for sids in concept_study_count.values()]
    return sum(freqs) / len(freqs)


# ---------- Refutational integration ----------

def _refutational_integration(themes, studies):
    """Proportion of themes with disconfirming evidence.

    A theme has disconfirming evidence if any study NOT assigned to it
    has findings that mention theme-related words but in a contradictory
    context (containing negation words).
    """
    if not themes:
        return 0.0

    negation_words = {"not", "no", "contrary", "despite", "however",
                      "never", "neither", "without", "fail", "lack",
                      "unable", "unlikely", "disagree", "contradict"}

    themes_with_disconfirm = 0

    for theme in themes:
        label_words = set(
            w.strip(".,;:!?\"'()-").lower()
            for w in theme.label.split()
            if len(w.strip(".,;:!?\"'()-")) > 2
        )
        if not label_words:
            continue

        has_disconfirm = False
        for study in studies:
            # Check studies NOT assigned to this theme
            if study.study_id in theme.assigned_studies:
                continue
            for finding in study.key_findings:
                lower = finding.lower()
                # Check if finding mentions theme
                mentions = any(w in lower for w in label_words)
                if mentions:
                    # Check for negation
                    words = lower.split()
                    if any(w.strip(".,;:!?\"'()-") in negation_words for w in words):
                        has_disconfirm = True
                        break
            if has_disconfirm:
                break

        if has_disconfirm:
            themes_with_disconfirm += 1

    return themes_with_disconfirm / len(themes)


# ---------- Development trajectory ----------

def _spearman_rank_correlation(x, y):
    """Compute Spearman rank correlation between two lists.

    Pure Python implementation using rank transformation.
    Returns correlation in [-1, 1], or 0.0 if degenerate.
    """
    n = len(x)
    if n < 2:
        return 0.0

    def _rank(values):
        """Assign ranks with average ties."""
        indexed = sorted(range(n), key=lambda i: values[i])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n - 1 and values[indexed[j + 1]] == values[indexed[j]]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1  # 1-based
            for k in range(i, j + 1):
                ranks[indexed[k]] = avg_rank
            i = j + 1
        return ranks

    rx = _rank(x)
    ry = _rank(y)

    # Pearson on ranks
    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n

    cov = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(n))
    var_x = sum((rx[i] - mean_rx) ** 2 for i in range(n))
    var_y = sum((ry[i] - mean_ry) ** 2 for i in range(n))

    denom = (var_x * var_y) ** 0.5
    if denom < 1e-15:
        return 0.0
    return cov / denom


def _development_trajectory(studies, themes):
    """Compute development trajectory correlation.

    If studies are ordered by year, compute Spearman rank correlation
    between study order and mean theme abstraction level for that study.
    """
    if len(studies) < 2 or not themes:
        return 0.0

    # Sort studies by year
    sorted_studies = sorted(studies, key=lambda s: s.year)

    # For each study, compute mean abstraction of its themes
    theme_levels = {}
    for t in themes:
        theme_levels[t.theme_id] = _classify_abstraction_level(t)

    study_abstraction = []
    for s in sorted_studies:
        assigned_themes = [
            t for t in themes if s.study_id in t.assigned_studies
        ]
        if assigned_themes:
            mean_abs = sum(
                theme_levels[t.theme_id] for t in assigned_themes
            ) / len(assigned_themes)
        else:
            mean_abs = 1.0  # default
        study_abstraction.append(mean_abs)

    study_order = list(range(len(sorted_studies)))
    return _spearman_rank_correlation(study_order, study_abstraction)


# ---------- Public API ----------

def analyse_conceptual_depth(studies, themes):
    """Measure interpretive depth and theoretical development.

    Args:
        studies: list of StudyInput
        themes: list of Theme

    Returns:
        dict with keys:
            theme_levels: dict theme_id -> int (1-4)
            mean_abstraction: float
            theoretical_reach: float (proportion >= level 3)
            coding_density: float
            hermeneutic_depth_index: float in [0, 1]
            development_correlation: float in [-1, 1]
            level_distribution: dict level(int) -> count
    """
    if not themes:
        return {
            "theme_levels": {},
            "mean_abstraction": 0.0,
            "theoretical_reach": 0.0,
            "coding_density": 0.0,
            "hermeneutic_depth_index": 0.0,
            "development_correlation": 0.0,
            "level_distribution": {1: 0, 2: 0, 3: 0, 4: 0},
        }

    # 1. Classify each theme
    theme_levels = {}
    for t in themes:
        theme_levels[t.theme_id] = _classify_abstraction_level(t)

    # Level distribution
    level_dist = {1: 0, 2: 0, 3: 0, 4: 0}
    for level in theme_levels.values():
        level_dist[level] = level_dist.get(level, 0) + 1

    # 2. Mean abstraction level
    mean_abstraction = sum(theme_levels.values()) / len(theme_levels)

    # 3. Theoretical reach: proportion of themes at level >= 3
    n_high = sum(1 for lv in theme_levels.values() if lv >= 3)
    theoretical_reach = n_high / len(themes)

    # 4. Coding density
    coding_density = _compute_coding_density(studies, themes)

    # 5. Theme hierarchy depth
    hierarchy_depth = _max_hierarchy_depth(themes)

    # 6. Cross-study concept recurrence
    concept_recur = _concept_recurrence(themes, studies)

    # 7. Refutational integration
    refut_integ = _refutational_integration(themes, studies)

    # 8. Hermeneutic depth index (weighted composite)
    #    - Mean abstraction level (normalized to 0-1 by /4): weight 0.3
    #    - Theme hierarchy depth (max chain / 4, capped at 1): weight 0.2
    #    - Coding density (capped at 1.0): weight 0.2
    #    - Cross-study concept recurrence: weight 0.15
    #    - Refutational integration: weight 0.15
    norm_abstraction = mean_abstraction / 4.0
    norm_hierarchy = min(hierarchy_depth / 4.0, 1.0)
    norm_density = min(coding_density, 1.0)
    norm_recurrence = min(concept_recur, 1.0)
    norm_refutation = min(refut_integ, 1.0)

    hdi = (
        0.30 * norm_abstraction
        + 0.20 * norm_hierarchy
        + 0.20 * norm_density
        + 0.15 * norm_recurrence
        + 0.15 * norm_refutation
    )

    # Clamp to [0, 1]
    hdi = max(0.0, min(1.0, hdi))

    # 9. Development trajectory
    dev_corr = _development_trajectory(studies, themes)

    return {
        "theme_levels": theme_levels,
        "mean_abstraction": mean_abstraction,
        "theoretical_reach": theoretical_reach,
        "coding_density": coding_density,
        "hermeneutic_depth_index": hdi,
        "development_correlation": dev_corr,
        "level_distribution": level_dist,
    }
