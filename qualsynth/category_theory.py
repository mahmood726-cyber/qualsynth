"""Category-Theoretic Theme Analysis.

Pure Python implementation. Models themes as objects in a category
where morphisms represent subsumption (study set inclusion),
computes products, coproducts, isomorphism classes, terminal/initial
objects, and adjunction scores.
"""


def _theme_study_sets(themes):
    """Build dict: theme_id -> set of assigned study_ids."""
    return {t.theme_id: set(t.assigned_studies) for t in themes}


def compute_morphisms(themes):
    """Compute morphisms (subsumption arrows) between themes.

    A -> B exists if A.studies is a subset of B.studies.
    Identity morphisms (A -> A) are always included.

    Returns:
        list of (source_theme_id, target_theme_id) tuples
    """
    study_sets = _theme_study_sets(themes)
    morphisms = []

    for ta in themes:
        # Identity
        morphisms.append((ta.theme_id, ta.theme_id))
        for tb in themes:
            if ta.theme_id != tb.theme_id:
                if study_sets[ta.theme_id] <= study_sets[tb.theme_id]:
                    morphisms.append((ta.theme_id, tb.theme_id))

    return morphisms


def compute_products(themes):
    """Compute categorical products: A x B = intersection of studies.

    Only includes products where intersection is non-empty.

    Returns:
        dict mapping (theme_id_a, theme_id_b) -> set of study_ids
    """
    study_sets = _theme_study_sets(themes)
    products = {}

    for i, ta in enumerate(themes):
        for j, tb in enumerate(themes):
            if i < j:
                inter = study_sets[ta.theme_id] & study_sets[tb.theme_id]
                if inter:
                    products[(ta.theme_id, tb.theme_id)] = inter

    return products


def compute_coproducts(themes):
    """Compute categorical coproducts: A + B = union of studies.

    Returns:
        dict mapping (theme_id_a, theme_id_b) -> set of study_ids
    """
    study_sets = _theme_study_sets(themes)
    coproducts = {}

    for i, ta in enumerate(themes):
        for j, tb in enumerate(themes):
            if i < j:
                union = study_sets[ta.theme_id] | study_sets[tb.theme_id]
                coproducts[(ta.theme_id, tb.theme_id)] = union

    return coproducts


def compute_isomorphism_classes(themes):
    """Group themes with identical study sets into isomorphism classes.

    Returns:
        list of lists of theme_ids (each inner list is an iso class)
    """
    study_sets = _theme_study_sets(themes)

    # Group by frozenset of studies
    groups = {}
    for t in themes:
        key = frozenset(study_sets[t.theme_id])
        if key not in groups:
            groups[key] = []
        groups[key].append(t.theme_id)

    return list(groups.values())


def find_terminal(themes):
    """Find terminal object: a theme whose study set contains all studies
    from every other theme (i.e., every theme's studies are a subset).

    Returns:
        theme_id or None
    """
    study_sets = _theme_study_sets(themes)
    all_studies = set()
    for s in study_sets.values():
        all_studies |= s

    for t in themes:
        if study_sets[t.theme_id] >= all_studies:
            return t.theme_id

    return None


def find_initial(themes):
    """Find initial object: a theme whose study set is a subset of
    every other theme's study set.

    Returns:
        theme_id or None
    """
    study_sets = _theme_study_sets(themes)

    for t in themes:
        is_initial = True
        for other in themes:
            if not (study_sets[t.theme_id] <= study_sets[other.theme_id]):
                is_initial = False
                break
        if is_initial:
            return t.theme_id

    return None


def compute_adjunction_score(themes):
    """Compute adjunction score: how well the Theme->Study and
    Study->Theme functors compose back to identity.

    Theme->Study: maps theme to its study set
    Study->Theme: maps study to set of themes containing it

    Score = fraction of themes where round-trip (theme -> studies -> themes)
    recovers at least the original theme.

    A score of 1.0 means perfect adjunction (every theme is recoverable).

    Returns:
        float in [0, 1]
    """
    if not themes:
        return 0.0

    study_sets = _theme_study_sets(themes)

    # Build inverse: study -> set of themes
    study_to_themes = {}
    for t in themes:
        for sid in t.assigned_studies:
            if sid not in study_to_themes:
                study_to_themes[sid] = set()
            study_to_themes[sid].add(t.theme_id)

    recoverable = 0
    for t in themes:
        # Round trip: theme -> its studies -> union of themes containing those studies
        round_trip_themes = set()
        for sid in t.assigned_studies:
            round_trip_themes |= study_to_themes.get(sid, set())

        # Check if original theme is recovered
        if t.theme_id in round_trip_themes:
            recoverable += 1

    return recoverable / len(themes)


def analyse_category(themes):
    """Full category-theoretic analysis of themes.

    Args:
        themes: list of Theme (with assigned_studies)

    Returns:
        dict with keys:
            morphisms: list of (source, target) tuples
            products: dict {(tid_a, tid_b): set of study_ids}
            coproducts: dict {(tid_a, tid_b): set of study_ids}
            n_iso_classes: int
            has_terminal: bool
            has_initial: bool
            adjunction_score: float in [0, 1]
    """
    morphisms = compute_morphisms(themes)
    products = compute_products(themes)
    coproducts = compute_coproducts(themes)
    iso_classes = compute_isomorphism_classes(themes)
    terminal = find_terminal(themes)
    initial = find_initial(themes)
    adj_score = compute_adjunction_score(themes)

    return {
        "morphisms": morphisms,
        "products": products,
        "coproducts": coproducts,
        "n_iso_classes": len(iso_classes),
        "has_terminal": terminal is not None,
        "has_initial": initial is not None,
        "adjunction_score": adj_score,
    }
