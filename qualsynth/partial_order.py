"""Partial Order and Lattice Analysis of themes.

Pure Python implementation (no numpy/scipy). Analyses the subsumption
structure of themes based on study assignments: theme A subsumes theme B
if B's assigned_studies is a subset of A's.  Computes Hasse diagram,
Moebius function, lattice properties, zeta polynomial, and dimension
upper bound.
"""


# ---------------------------------------------------------------------------
# Subsumption and Hasse diagram
# ---------------------------------------------------------------------------

def _build_subsumption(themes):
    """Build the subsumption partial order.

    Returns:
        ids: list of theme_id (in original order)
        study_sets: dict theme_id -> set of study_ids
        order: list of (parent_id, child_id) where parent subsumes child
               (child's studies subset of parent's studies)
    """
    ids = [t.theme_id for t in themes]
    study_sets = {t.theme_id: set(t.assigned_studies) for t in themes}

    order = []
    for a in ids:
        for b in ids:
            if a == b:
                continue
            # A subsumes B iff B's studies are a subset of A's studies
            if study_sets[b] and study_sets[b] <= study_sets[a]:
                order.append((a, b))

    return ids, study_sets, order


def _hasse_edges(ids, order):
    """Remove transitive edges to produce the Hasse diagram.

    Edge (A, B) is kept iff A subsumes B and there is no intermediate C
    such that A subsumes C and C subsumes B.
    """
    order_set = set(order)
    hasse = []
    for (a, b) in order:
        # Check if there is a C such that (a, c) and (c, b) both in order
        transitive = False
        for c in ids:
            if c == a or c == b:
                continue
            if (a, c) in order_set and (c, b) in order_set:
                transitive = True
                break
        if not transitive:
            hasse.append({"parent": a, "child": b})
    return hasse


# ---------------------------------------------------------------------------
# Moebius function
# ---------------------------------------------------------------------------

def _comparable_pairs(ids, order):
    """Return set of (x, y) where x <= y in the partial order (including x==x)."""
    order_set = set(order)
    pairs = set()
    for x in ids:
        pairs.add((x, x))
    for (a, b) in order_set:
        pairs.add((a, b))
    return pairs


def _moebius_function(ids, order):
    """Compute the Moebius function mu(x, y) for all comparable pairs.

    mu(x, x) = 1
    mu(x, y) = -sum_{x <= z < y} mu(x, z)  for x < y
    """
    comparable = _comparable_pairs(ids, order)
    order_set = set(order)

    # Build a mapping of what each element covers (x < y means (x,y) in order
    # but here x is the parent that subsumes y... Actually the partial order
    # relation is: A >= B when A subsumes B. So the "less than" direction
    # for a standard poset is: B <= A when A subsumes B.
    # Let's define: x <= y iff y subsumes x (or x == y).
    # So (a, b) in 'order' means a subsumes b, i.e. b <= a in the poset.

    # Rewrite comparable: x <= y means y subsumes x, i.e. (y, x) in order, or x == y.
    poset_leq = set()
    for x in ids:
        poset_leq.add((x, x))
    for (a, b) in order_set:
        # a subsumes b => b <= a
        poset_leq.add((b, a))

    # mu(x, y) for x <= y
    mu = {}
    for x in ids:
        mu[(x, x)] = 1

    # We need topological processing. For each pair (x, y) with x < y:
    # mu(x, y) = -sum_{x <= z < y} mu(x, z)
    # Process by "distance" (number of intermediate elements).

    # Build adjacency for the poset (covers relation)
    # z < y means z != y and z <= y
    strictly_less = {}
    for x in ids:
        strictly_less[x] = []
    for (x, y) in poset_leq:
        if x != y:
            strictly_less[y].append(x)

    # For each x, do BFS/DFS upward to compute mu(x, y) for all y >= x
    for x in ids:
        # Find all y such that x <= y, ordered by "distance" from x
        # Use BFS from x going upward
        visited = {x}
        queue = [x]
        topo_order = [x]
        while queue:
            current = queue.pop(0)
            # Find all y such that current < y (current is strictly less than y)
            for y in ids:
                if y not in visited and (current, y) in poset_leq and current != y:
                    # Check we haven't seen y yet
                    # But we need to process in topological order
                    pass

        # Simpler approach: topological sort of all elements >= x
        reachable = set()
        _find_reachable_up(x, ids, poset_leq, reachable)

        # Topological sort: process elements by number of predecessors that are >= x
        # Use Kahn's algorithm on the subgraph
        reachable_list = sorted(reachable)
        # Count in-edges within reachable set (from below)
        in_degree = {v: 0 for v in reachable_list}
        edges = []
        for a in reachable_list:
            for b in reachable_list:
                if a != b and (a, b) in poset_leq:
                    # a < b in poset
                    edges.append((a, b))
                    in_degree[b] = in_degree.get(b, 0) + 1

        queue = [v for v in reachable_list if in_degree[v] == 0]
        topo = []
        while queue:
            queue.sort()  # deterministic
            v = queue.pop(0)
            topo.append(v)
            for (a, b) in edges:
                if a == v:
                    in_degree[b] -= 1
                    if in_degree[b] == 0:
                        queue.append(b)

        # Now compute mu(x, y) in topological order
        for y in topo:
            if y == x:
                continue
            if (x, y) not in poset_leq:
                continue
            # mu(x, y) = -sum_{x <= z < y} mu(x, z)
            s = 0
            for z in topo:
                if z == y:
                    continue
                if (x, z) in poset_leq and (z, y) in poset_leq and z != y:
                    s += mu.get((x, z), 0)
            mu[(x, y)] = -s

    return mu


def _find_reachable_up(x, ids, poset_leq, reachable):
    """Find all elements y such that x <= y."""
    reachable.add(x)
    for y in ids:
        if y not in reachable and (x, y) in poset_leq and x != y:
            _find_reachable_up(y, ids, poset_leq, reachable)


# ---------------------------------------------------------------------------
# Lattice properties
# ---------------------------------------------------------------------------

def _is_lattice(ids, order):
    """Check if the poset is a lattice (every pair has a join and meet)."""
    order_set = set(order)

    # Build poset_leq: x <= y iff y subsumes x or x == y
    poset_leq = set()
    for x in ids:
        poset_leq.add((x, x))
    for (a, b) in order_set:
        poset_leq.add((b, a))

    def upper_bounds(a, b):
        """Elements >= both a and b."""
        return [z for z in ids if (a, z) in poset_leq and (b, z) in poset_leq]

    def lower_bounds(a, b):
        """Elements <= both a and b."""
        return [z for z in ids if (z, a) in poset_leq and (z, b) in poset_leq]

    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            ub = upper_bounds(a, b)
            lb = lower_bounds(a, b)
            if not ub or not lb:
                return False
            # Check for least upper bound (join)
            join_candidates = [u for u in ub
                               if all((u, v) in poset_leq or u == v for v in ub)]
            if not join_candidates:
                return False
            # Check for greatest lower bound (meet)
            meet_candidates = [l for l in lb
                               if all((v, l) in poset_leq or v == l for v in lb)]
            if not meet_candidates:
                return False

    return True


def _longest_chain(ids, order):
    """Find the height (length of the longest chain) in the poset."""
    order_set = set(order)
    poset_leq = set()
    for x in ids:
        poset_leq.add((x, x))
    for (a, b) in order_set:
        poset_leq.add((b, a))

    # Build DAG edges: x -> y means x < y (x is strictly less than y)
    edges = {}
    for x in ids:
        edges[x] = []
    for x in ids:
        for y in ids:
            if x != y and (x, y) in poset_leq:
                edges[x].append(y)

    # Longest path via DFS + memoization
    memo = {}

    def dfs(node):
        if node in memo:
            return memo[node]
        best = 0
        for nxt in edges[node]:
            best = max(best, 1 + dfs(nxt))
        memo[node] = best
        return best

    height = 0
    for x in ids:
        height = max(height, dfs(x))
    return height


def _width_greedy(ids, order):
    """Approximate the width (largest antichain) using greedy chain decomposition.

    By Dilworth's theorem, width = minimum number of chains needed to
    cover all elements.  We approximate with a greedy approach.
    """
    order_set = set(order)
    poset_leq = set()
    for x in ids:
        poset_leq.add((x, x))
    for (a, b) in order_set:
        poset_leq.add((b, a))

    remaining = set(ids)
    chains = []

    while remaining:
        # Build a chain greedily: start with a minimal element, extend upward
        # Find a minimal element (no z < x in remaining)
        minimal = None
        for x in sorted(remaining):
            is_min = True
            for z in remaining:
                if z != x and (z, x) in poset_leq:
                    is_min = False
                    break
            if is_min:
                minimal = x
                break
        if minimal is None:
            minimal = sorted(remaining)[0]

        chain = [minimal]
        remaining.remove(minimal)

        # Extend chain upward
        while True:
            # Find a minimal element in remaining that is >= last chain element
            last = chain[-1]
            candidates = sorted([z for z in remaining if (last, z) in poset_leq])
            if not candidates:
                break
            # Pick the one that is minimal among candidates
            chosen = None
            for c in candidates:
                is_min = True
                for d in candidates:
                    if d != c and (d, c) in poset_leq and d != c:
                        is_min = False
                        break
                if is_min:
                    chosen = c
                    break
            if chosen is None:
                break
            chain.append(chosen)
            remaining.remove(chosen)

        chains.append(chain)

    return len(chains)


def _density(ids, order):
    """Fraction of comparable pairs among all distinct pairs."""
    n = len(ids)
    if n < 2:
        return 0.0
    total_pairs = n * (n - 1) / 2
    n_comparable = len(order)  # each (a,b) is a directed comparable pair
    # But order has directed pairs; count undirected comparable pairs
    undirected = set()
    for (a, b) in order:
        pair = tuple(sorted([a, b]))
        undirected.add(pair)
    return len(undirected) / total_pairs if total_pairs > 0 else 0.0


# ---------------------------------------------------------------------------
# Zeta polynomial
# ---------------------------------------------------------------------------

def _zeta_polynomial(ids, order, max_n=3):
    """Compute Z(n) = number of multichains of length n.

    Z(1) = number of elements
    Z(2) = number of comparable pairs (including (x,x))
    Z(n) = number of chains x_1 <= x_2 <= ... <= x_n
    """
    order_set = set(order)
    poset_leq = set()
    for x in ids:
        poset_leq.add((x, x))
    for (a, b) in order_set:
        poset_leq.add((b, a))

    zeta = {}
    elements = list(ids)

    zeta[1] = len(elements)

    if max_n >= 2:
        # Z(2) = number of pairs (x, y) with x <= y (including x == y)
        count = 0
        for x in elements:
            for y in elements:
                if (x, y) in poset_leq:
                    count += 1
        zeta[2] = count

    if max_n >= 3:
        # Z(3) = number of triples (x, y, z) with x <= y <= z
        count = 0
        for x in elements:
            for y in elements:
                if (x, y) not in poset_leq:
                    continue
                for z in elements:
                    if (y, z) in poset_leq:
                        count += 1
        zeta[3] = count

    return zeta


# ---------------------------------------------------------------------------
# Dimension upper bound
# ---------------------------------------------------------------------------

def _dimension_upper_bound(ids, order):
    """Upper bound on the order dimension.

    If width <= 2, dimension <= 2; otherwise dimension <= width.
    """
    w = _width_greedy(ids, order)
    return min(w, max(w, 2))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyse_partial_order(themes):
    """Analyse the partial order of themes based on study assignment subsumption.

    Args:
        themes: list of Theme objects (must have theme_id, assigned_studies).

    Returns:
        dict with keys:
            hasse_edges: list of {parent, child} theme_ids
            width: int (size of largest antichain, approximate)
            height: int (length of longest chain)
            density: float (comparable pairs / total pairs)
            is_lattice: bool
            moebius_values: dict of (theme_a, theme_b) -> int
            dimension_upper_bound: int
            n_comparable_pairs: int
            zeta_values: dict n -> count for n=1,2,3
    """
    if not themes:
        return {
            "hasse_edges": [],
            "width": 0,
            "height": 0,
            "density": 0.0,
            "is_lattice": True,
            "moebius_values": {},
            "dimension_upper_bound": 0,
            "n_comparable_pairs": 0,
            "zeta_values": {1: 0, 2: 0, 3: 0},
        }

    ids, study_sets, order = _build_subsumption(themes)

    hasse = _hasse_edges(ids, order)
    height = _longest_chain(ids, order)
    width = _width_greedy(ids, order)
    dens = _density(ids, order)
    lattice = _is_lattice(ids, order)
    moebius = _moebius_function(ids, order)
    dim = _dimension_upper_bound(ids, order)
    zeta = _zeta_polynomial(ids, order, max_n=3)

    # Count undirected comparable pairs (excluding self-pairs)
    undirected = set()
    for (a, b) in order:
        pair = tuple(sorted([a, b]))
        undirected.add(pair)

    # Convert moebius keys to serialisable format
    moebius_out = {}
    for (a, b), val in moebius.items():
        moebius_out[(a, b)] = val

    return {
        "hasse_edges": hasse,
        "width": width,
        "height": height,
        "density": dens,
        "is_lattice": lattice,
        "moebius_values": moebius_out,
        "dimension_upper_bound": dim,
        "n_comparable_pairs": len(undirected),
        "zeta_values": zeta,
    }
