"""Formal Concept Analysis for qualitative evidence synthesis.

Pure Python implementation (no numpy/scipy). Builds a concept lattice
from the study x theme incidence relation, computes Hasse diagram,
extracts implications, and reports lattice metrics.
"""


def _build_incidence(studies, themes):
    """Build study x theme binary incidence matrix.

    Returns:
        G: list of study_ids (objects)
        M: list of theme_ids (attributes)
        I: dict of (g, m) -> True for each incidence
    """
    G = [s.study_id for s in studies]
    M = [t.theme_id for t in themes]
    # Build theme -> set of assigned studies
    theme_study_map = {}
    for t in themes:
        theme_study_map[t.theme_id] = set(t.assigned_studies)

    I = {}
    for g in G:
        for m in M:
            if g in theme_study_map.get(m, set()):
                I[(g, m)] = True
    return G, M, I


def _derive_themes(A, M, I):
    """A' = {m in M : for all g in A, (g,m) in I} — themes common to all studies in A."""
    if not A:
        return frozenset(M)
    result = []
    for m in M:
        if all((g, m) in I for g in A):
            result.append(m)
    return frozenset(result)


def _derive_studies(B, G, I):
    """B' = {g in G : for all m in B, (g,m) in I} — studies having all themes in B."""
    if not B:
        return frozenset(G)
    result = []
    for g in G:
        if all((g, m) in I for m in B):
            result.append(g)
    return frozenset(result)


def _closure(B, G, M, I):
    """Compute closure of a set of themes B: B'' = (B')' ."""
    studies = _derive_studies(B, G, I)
    return _derive_themes(studies, M, I)


def _enumerate_concepts_brute(G, M, I):
    """Enumerate all formal concepts by iterating over theme subsets.

    For |M| <= 15, enumerate all 2^|M| subsets.
    Returns list of (extent: frozenset, intent: frozenset).
    """
    M_list = list(M) if not isinstance(M, list) else M
    n = len(M_list)
    concepts = set()

    for mask in range(1 << n):
        B = frozenset(M_list[i] for i in range(n) if mask & (1 << i))
        # Compute closure
        studies = _derive_studies(B, G, I)
        intent = _derive_themes(studies, M_list, I)
        extent = _derive_studies(intent, G, I)
        concepts.add((extent, intent))

    # Also add the top concept: ({all_studies}', {all_studies}'')
    all_themes = _derive_themes(G, M_list, I)
    all_studies = _derive_studies(all_themes, G, I)
    concepts.add((all_studies, all_themes))

    # And the bottom concept: (M', M'')
    bottom_extent = _derive_studies(frozenset(M_list), G, I)
    bottom_intent = _derive_themes(bottom_extent, M_list, I)
    concepts.add((bottom_extent, bottom_intent))

    return list(concepts)


def _cbo_concepts(G, M, I):
    """Close by One (CbO) algorithm for larger attribute sets.

    Incrementally extends concepts by adding one attribute at a time.
    More efficient than brute force for |M| > 12.
    """
    M_list = list(M) if not isinstance(M, list) else M
    concepts = []
    seen = set()

    def _cbo(extent, intent, start_idx):
        key = (extent, intent)
        if key in seen:
            return
        seen.add(key)
        concepts.append((extent, intent))

        for j in range(start_idx, len(M_list)):
            m = M_list[j]
            if m in intent:
                continue
            # New intent candidate
            new_intent = intent | frozenset([m])
            new_extent = _derive_studies(new_intent, G, I)
            closed_intent = _derive_themes(new_extent, M_list, I)

            # Canonicity test: the closure should not add any attribute
            # that comes before position j in the ordering
            canonical = True
            for i in range(j):
                if M_list[i] in closed_intent and M_list[i] not in intent:
                    canonical = False
                    break

            if canonical:
                _cbo(new_extent, closed_intent, j + 1)

    # Start with the top concept
    top_intent = _derive_themes(G, M_list, I)
    top_extent = _derive_studies(top_intent, G, I)
    _cbo(top_extent, top_intent, 0)

    return concepts


def _compute_hasse_edges(concepts):
    """Compute Hasse diagram edges (direct cover relations).

    (A1,B1) <= (A2,B2) iff A1 subset of A2.
    An edge is direct if there is no intermediate concept.

    Returns list of (parent_idx, child_idx) where parent has larger extent.
    """
    n = len(concepts)
    # Sort by extent size descending (larger extent = higher in lattice)
    indices = list(range(n))

    # Check subconcept relation
    # (A1,B1) < (A2,B2) iff A1 strictly subset of A2
    edges = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            ext_i = concepts[i][0]
            ext_j = concepts[j][0]
            if ext_i < ext_j:  # strict subset: i is below j
                # Check if direct: no k with ext_i < ext_k < ext_j
                is_direct = True
                for k in range(n):
                    if k == i or k == j:
                        continue
                    ext_k = concepts[k][0]
                    if ext_i < ext_k and ext_k < ext_j:
                        is_direct = False
                        break
                if is_direct:
                    edges.append((j, i))  # parent=j (larger), child=i (smaller)

    return edges


def _find_implications(G, M, I):
    """Find exact implications (confidence = 1.0).

    An implication B -> m holds if every study having all themes in B
    also has theme m (and m not in B).

    Returns list of {antecedent, consequent, support}.
    """
    M_list = list(M) if not isinstance(M, list) else M
    implications = []

    # For efficiency, only check single-attribute and pair antecedents
    # (full enumeration for small M)
    n = len(M_list)
    max_ante = min(n, 4)  # limit antecedent size

    for size in range(1, max_ante + 1):
        for ante_set in _combinations(M_list, size):
            ante = frozenset(ante_set)
            # Studies having all themes in ante
            supporting = [g for g in G if all((g, m) in I for m in ante)]
            if not supporting:
                continue
            support = len(supporting)

            for m in M_list:
                if m in ante:
                    continue
                # Check if all supporting studies also have m
                if all((g, m) in I for g in supporting):
                    implications.append({
                        "antecedent": sorted(ante),
                        "consequent": m,
                        "support": support,
                    })

    return implications


def _combinations(items, r):
    """Generate all r-combinations from items (pure Python)."""
    n = len(items)
    if r > n:
        return
    indices = list(range(r))
    yield tuple(items[i] for i in indices)
    while True:
        found = False
        for i in range(r - 1, -1, -1):
            if indices[i] != i + n - r:
                found = True
                break
        if not found:
            return
        indices[i] += 1
        for j in range(i + 1, r):
            indices[j] = indices[j - 1] + 1
        yield tuple(items[i] for i in indices)


def _lattice_width(concepts):
    """Compute lattice width: size of the largest antichain.

    An antichain is a set of concepts where no two are comparable
    (neither is a subconcept of the other).

    Uses greedy approach: Dilworth's theorem relates width to min
    chain decomposition, but for small lattices we check directly.
    """
    n = len(concepts)
    if n == 0:
        return 0

    # Build comparability: i < j if extent_i strict subset of extent_j
    comparable = [[False] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                if concepts[i][0] < concepts[j][0] or concepts[j][0] < concepts[i][0]:
                    comparable[i][j] = True

    # Find maximum antichain (greedy: pick node with fewest comparable nodes)
    best_size = 1
    # For small n, try all subsets up to a reasonable limit
    if n <= 20:
        # Greedy antichain construction
        remaining = set(range(n))
        antichain = []
        while remaining:
            # Pick node incomparable with current antichain
            found = False
            for node in sorted(remaining):
                ok = True
                for a in antichain:
                    if comparable[node][a]:
                        ok = False
                        break
                if ok:
                    antichain.append(node)
                    remaining.discard(node)
                    found = True
                    break
            if not found:
                break
        best_size = max(best_size, len(antichain))

        # Also try starting from each node
        for start in range(n):
            antichain = [start]
            for node in range(n):
                if node == start:
                    continue
                ok = True
                for a in antichain:
                    if comparable[node][a]:
                        ok = False
                        break
                if ok:
                    antichain.append(node)
            best_size = max(best_size, len(antichain))

    return best_size


def _lattice_height(concepts):
    """Compute lattice height: length of the longest chain.

    A chain is a sequence c0 < c1 < ... < ck where each is a subconcept.
    Height = k (number of edges in longest chain).
    """
    n = len(concepts)
    if n <= 1:
        return 0

    # Build subconcept graph
    # i -> j means concepts[i] < concepts[j] (i has strictly smaller extent)
    children = [[] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j and concepts[i][0] < concepts[j][0]:
                children[i].append(j)

    # Find longest path using DFS with memoization
    memo = {}

    def _longest_up(node):
        if node in memo:
            return memo[node]
        best = 0
        for ch in children[node]:
            best = max(best, 1 + _longest_up(ch))
        memo[node] = best
        return best

    height = 0
    for i in range(n):
        height = max(height, _longest_up(i))

    return height


# ---------- Public API ----------

def analyse_formal_concepts(studies, themes):
    """Build and analyse the formal concept lattice from study x theme incidence.

    Args:
        studies: list of StudyInput
        themes: list of Theme (with assigned_studies populated)

    Returns:
        dict with keys:
            concepts: list of {extent: list, intent: list}
            n_concepts: int
            implications: list of {antecedent, consequent, support}
            lattice_width: int
            lattice_height: int
            hasse_edges: list of {parent, child} as concept indices
    """
    if not studies or not themes:
        return {
            "concepts": [],
            "n_concepts": 0,
            "implications": [],
            "lattice_width": 0,
            "lattice_height": 0,
            "hasse_edges": [],
        }

    G, M, I = _build_incidence(studies, themes)

    # Choose algorithm based on attribute count
    n_attrs = len(M)
    if n_attrs <= 12:
        raw_concepts = _enumerate_concepts_brute(G, M, I)
    else:
        raw_concepts = _cbo_concepts(G, M, I)

    # Deduplicate (set of frozensets)
    seen = set()
    concepts = []
    for ext, intent in raw_concepts:
        key = (ext, intent)
        if key not in seen:
            seen.add(key)
            concepts.append((ext, intent))

    # Sort by extent size descending for consistent ordering
    concepts.sort(key=lambda c: (-len(c[0]), sorted(c[1])))

    # Compute Hasse edges
    hasse = _compute_hasse_edges(concepts)

    # Find implications
    implications = _find_implications(G, M, I)

    # Lattice metrics
    width = _lattice_width(concepts)
    height = _lattice_height(concepts)

    # Format output
    concepts_out = [
        {"extent": sorted(ext), "intent": sorted(intent)}
        for ext, intent in concepts
    ]
    hasse_out = [
        {"parent": p, "child": c}
        for p, c in hasse
    ]

    return {
        "concepts": concepts_out,
        "n_concepts": len(concepts),
        "implications": implications,
        "lattice_width": width,
        "lattice_height": height,
        "hasse_edges": hasse_out,
    }
