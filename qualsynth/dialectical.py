"""Dialectical Analysis: Thesis-Antithesis-Synthesis for qualitative evidence.

Pure Python implementation (no numpy/scipy). Detects contradictions and
resolutions in qualitative findings by analysing polarity of themes,
identifying antithetical pairs, and locating synthesis themes.
"""

from qualsynth.similarity import _tokenize

# Indicator word lists
POSITIVE_INDICATORS = frozenset([
    "benefit", "effective", "helpful", "positive", "support",
    "facilitate", "enable", "improve", "advantage", "success",
    "beneficial", "facilitates", "enables", "improves", "supports",
    "supported", "helped", "improved", "enabled", "facilitated",
])

NEGATIVE_INDICATORS = frozenset([
    "barrier", "challenge", "difficult", "negative", "hinder",
    "prevent", "obstacle", "limit", "burden", "problem",
    "barriers", "challenges", "difficulties", "hinders", "prevents",
    "obstacles", "limits", "limited", "hindered", "prevented",
])


def _get_theme_findings(theme, studies):
    """Get all key_findings text from studies assigned to this theme.

    Returns list of strings (individual findings).
    """
    assigned = set(theme.assigned_studies)
    findings = []
    for s in studies:
        if s.study_id in assigned:
            findings.extend(s.key_findings)
    return findings


def _compute_polarity(findings):
    """Compute polarity score from a list of findings text.

    Polarity = (positive_count - negative_count) / total_count
    where total_count = positive_count + negative_count.
    Returns value in [-1, 1], or 0.0 if no indicators found.
    """
    pos_count = 0
    neg_count = 0

    for text in findings:
        tokens = set(_tokenize(text))
        pos_count += len(tokens & POSITIVE_INDICATORS)
        neg_count += len(tokens & NEGATIVE_INDICATORS)

    total = pos_count + neg_count
    if total == 0:
        return 0.0
    return (pos_count - neg_count) / total


def _detect_antithetical_pairs(theme_polarities, themes):
    """Find theme pairs with opposing polarities.

    Returns list of {thesis, antithesis, strength} dicts.
    Thesis is the theme with positive polarity, antithesis the negative one.
    """
    pairs = []
    theme_ids = [t.theme_id for t in themes]

    for i in range(len(theme_ids)):
        for j in range(i + 1, len(theme_ids)):
            tid_i = theme_ids[i]
            tid_j = theme_ids[j]
            pol_i = theme_polarities.get(tid_i, 0.0)
            pol_j = theme_polarities.get(tid_j, 0.0)

            if pol_i * pol_j < 0:  # opposite signs
                strength = abs(pol_i - pol_j) / 2.0
                # Assign thesis (positive) and antithesis (negative)
                if pol_i >= pol_j:
                    thesis, antithesis = tid_i, tid_j
                else:
                    thesis, antithesis = tid_j, tid_i
                pairs.append({
                    "thesis": thesis,
                    "antithesis": antithesis,
                    "strength": round(strength, 4),
                })

    return pairs


def _detect_syntheses(antithetical_pairs, themes):
    """Find synthesis themes that bridge antithetical pairs.

    A synthesis theme has assigned_studies overlapping with BOTH
    the thesis and antithesis themes.

    Returns list of {thesis, antithesis, synthesis_theme, completeness} dicts.
    """
    # Build theme_id -> set of assigned studies
    theme_studies = {}
    for t in themes:
        theme_studies[t.theme_id] = set(t.assigned_studies)

    syntheses = []
    for pair in antithetical_pairs:
        thesis_id = pair["thesis"]
        antithesis_id = pair["antithesis"]
        thesis_studies = theme_studies.get(thesis_id, set())
        antithesis_studies = theme_studies.get(antithesis_id, set())

        if not thesis_studies or not antithesis_studies:
            continue

        # Look for synthesis themes
        for t in themes:
            if t.theme_id == thesis_id or t.theme_id == antithesis_id:
                continue
            t_studies = theme_studies.get(t.theme_id, set())
            overlap_thesis = t_studies & thesis_studies
            overlap_antithesis = t_studies & antithesis_studies

            if overlap_thesis and overlap_antithesis:
                # Completeness: proportion of union studies covered
                union_studies = thesis_studies | antithesis_studies
                covered = (overlap_thesis | overlap_antithesis)
                completeness = len(covered) / len(union_studies) if union_studies else 0.0

                syntheses.append({
                    "thesis": thesis_id,
                    "antithesis": antithesis_id,
                    "synthesis_theme": t.theme_id,
                    "completeness": round(completeness, 4),
                })

    return syntheses


def _build_contradiction_matrix(themes, theme_polarities, antithetical_pairs, syntheses):
    """Build matrix of theme pairs with dialectical relationships.

    Relationship types:
        - "concordant": same polarity direction (or both zero)
        - "contradictory": opposite polarity, no synthesis found
        - "synthesized": opposite polarity with synthesis theme found

    Returns dict of (theme1, theme2) -> relationship string.
    """
    # Build lookup for antithetical pairs
    antithetical_set = set()
    for pair in antithetical_pairs:
        key = tuple(sorted([pair["thesis"], pair["antithesis"]]))
        antithetical_set.add(key)

    # Build lookup for synthesized pairs
    synthesized_set = set()
    for syn in syntheses:
        key = tuple(sorted([syn["thesis"], syn["antithesis"]]))
        synthesized_set.add(key)

    matrix = {}
    theme_ids = [t.theme_id for t in themes]

    for i in range(len(theme_ids)):
        for j in range(i + 1, len(theme_ids)):
            tid_i = theme_ids[i]
            tid_j = theme_ids[j]
            key = tuple(sorted([tid_i, tid_j]))

            if key in synthesized_set:
                relationship = "synthesized"
            elif key in antithetical_set:
                relationship = "contradictory"
            else:
                relationship = "concordant"

            matrix[(tid_i, tid_j)] = relationship

    return matrix


def _dialectical_depth(antithetical_pairs, syntheses, n_themes):
    """Compute dialectical depth: triads found / total possible.

    Total possible triads = number of antithetical pairs (each could have a synthesis).
    Depth = number of pairs that have at least one synthesis / total antithetical pairs.
    """
    if not antithetical_pairs:
        return 0.0

    # Count unique antithetical pairs that have at least one synthesis
    synthesized_pairs = set()
    for syn in syntheses:
        key = tuple(sorted([syn["thesis"], syn["antithesis"]]))
        synthesized_pairs.add(key)

    return len(synthesized_pairs) / len(antithetical_pairs)


def _resolution_score(antithetical_pairs, syntheses, themes):
    """Compute resolution score: average proportion of studies contributing to synthesis.

    For each contradiction (antithetical pair), find what proportion of
    the combined studies are covered by synthesis themes.
    """
    if not antithetical_pairs:
        return 0.0

    theme_studies = {}
    for t in themes:
        theme_studies[t.theme_id] = set(t.assigned_studies)

    # Group syntheses by antithetical pair
    pair_syntheses = {}
    for syn in syntheses:
        key = tuple(sorted([syn["thesis"], syn["antithesis"]]))
        if key not in pair_syntheses:
            pair_syntheses[key] = []
        pair_syntheses[key].append(syn["synthesis_theme"])

    scores = []
    for pair in antithetical_pairs:
        key = tuple(sorted([pair["thesis"], pair["antithesis"]]))
        thesis_studies = theme_studies.get(pair["thesis"], set())
        antithesis_studies = theme_studies.get(pair["antithesis"], set())
        union = thesis_studies | antithesis_studies

        if not union:
            scores.append(0.0)
            continue

        synth_themes = pair_syntheses.get(key, [])
        if not synth_themes:
            scores.append(0.0)
            continue

        # Studies covered by synthesis themes
        covered = set()
        for st_id in synth_themes:
            covered |= (theme_studies.get(st_id, set()) & union)

        scores.append(len(covered) / len(union))

    return sum(scores) / len(scores) if scores else 0.0


# ---------- Public API ----------

def analyse_dialectical(studies, themes):
    """Detect and structure contradictions and resolutions in qualitative evidence.

    Args:
        studies: list of StudyInput
        themes: list of Theme (with assigned_studies populated)

    Returns:
        dict with keys:
            theme_polarities: dict {theme_id: float in [-1, 1]}
            antithetical_pairs: list of {thesis, antithesis, strength}
            syntheses: list of {thesis, antithesis, synthesis_theme, completeness}
            dialectical_depth: float in [0, 1]
            resolution_score: float in [0, 1]
            contradiction_matrix: dict of (theme1, theme2) -> relationship_str
    """
    if not studies or not themes:
        return {
            "theme_polarities": {},
            "antithetical_pairs": [],
            "syntheses": [],
            "dialectical_depth": 0.0,
            "resolution_score": 0.0,
            "contradiction_matrix": {},
        }

    # Step 1: Compute polarity for each theme
    theme_polarities = {}
    for t in themes:
        findings = _get_theme_findings(t, studies)
        theme_polarities[t.theme_id] = round(_compute_polarity(findings), 4)

    # Step 2: Detect antithetical pairs
    antithetical_pairs = _detect_antithetical_pairs(theme_polarities, themes)

    # Step 3: Detect syntheses
    syntheses = _detect_syntheses(antithetical_pairs, themes)

    # Step 4: Build contradiction matrix
    contradiction_matrix = _build_contradiction_matrix(
        themes, theme_polarities, antithetical_pairs, syntheses
    )

    # Step 5: Compute metrics
    depth = _dialectical_depth(antithetical_pairs, syntheses, len(themes))
    resolution = _resolution_score(antithetical_pairs, syntheses, themes)

    return {
        "theme_polarities": theme_polarities,
        "antithetical_pairs": antithetical_pairs,
        "syntheses": syntheses,
        "dialectical_depth": round(depth, 4),
        "resolution_score": round(resolution, 4),
        "contradiction_matrix": contradiction_matrix,
    }
