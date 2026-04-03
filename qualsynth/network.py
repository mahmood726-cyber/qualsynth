"""Theme Co-occurrence Network Analysis.

Pure Python implementation — builds and analyses a graph of theme
relationships based on study-level co-occurrence.  Includes degree,
betweenness, closeness centrality, bridging-theme detection, and
greedy modularity-based community detection.
"""

from collections import deque


# ---------- Co-occurrence ----------

def _build_cooccurrence(themes, study_ids=None):
    """Build theme × theme co-occurrence matrix.

    Cell (i, j) = number of studies where both theme i and theme j
    have at least one assigned study.

    Args:
        themes: list of Theme
        study_ids: optional set of study_ids to restrict to.

    Returns:
        matrix: list-of-lists (k × k)
        theme_ids: list of theme_id strings
    """
    k = len(themes)
    theme_ids = [t.theme_id for t in themes]

    # For each theme, set of studies
    theme_studies = []
    for t in themes:
        s_set = set(t.assigned_studies)
        if study_ids is not None:
            s_set &= study_ids
        theme_studies.append(s_set)

    matrix = [[0] * k for _ in range(k)]
    for i in range(k):
        for j in range(i, k):
            count = len(theme_studies[i] & theme_studies[j])
            matrix[i][j] = count
            matrix[j][i] = count

    return matrix, theme_ids


# ---------- BFS shortest paths ----------

def _bfs_distances(adj, source):
    """BFS from source node, return dict {node: distance}."""
    k = len(adj)
    dist = [-1] * k
    dist[source] = 0
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in range(k):
            if adj[u][v] and dist[v] == -1:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def _bfs_all_shortest_paths(adj, source, k):
    """BFS from source, count number of shortest paths through each node.

    Returns:
        dist: list of distances (-1 if unreachable)
        n_paths: list of counts of shortest paths from source to each node
        pred: list of lists of predecessors on shortest paths
    """
    dist = [-1] * k
    n_paths = [0] * k
    pred = [[] for _ in range(k)]

    dist[source] = 0
    n_paths[source] = 1
    queue = deque([source])

    while queue:
        u = queue.popleft()
        for v in range(k):
            if not adj[u][v]:
                continue
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                n_paths[v] = n_paths[u]
                pred[v] = [u]
                queue.append(v)
            elif dist[v] == dist[u] + 1:
                n_paths[v] += n_paths[u]
                pred[v].append(u)

    return dist, n_paths, pred


# ---------- Centrality ----------

def _degree_centrality(adj):
    """Degree centrality: number of connections / (k-1)."""
    k = len(adj)
    result = {}
    for i in range(k):
        degree = sum(1 for j in range(k) if j != i and adj[i][j])
        result[i] = degree / (k - 1) if k > 1 else 0.0
    return result


def _betweenness_centrality(adj):
    """Betweenness centrality (Brandes-style with BFS).

    For each node t, count fraction of shortest paths between all
    other pairs (s, v) that pass through t.  Normalized by
    (n-1)(n-2)/2 for undirected graphs.
    """
    k = len(adj)
    bc = [0.0] * k

    for s in range(k):
        dist, n_paths, pred = _bfs_all_shortest_paths(adj, s, k)

        # Accumulate dependency (Brandes algorithm)
        delta = [0.0] * k
        # Process nodes in order of decreasing distance
        nodes_by_dist = sorted(range(k), key=lambda x: -dist[x])

        for w in nodes_by_dist:
            if dist[w] <= 0:
                continue  # source or unreachable
            for u in pred[w]:
                if n_paths[w] > 0:
                    frac = n_paths[u] / n_paths[w]
                    delta[u] += frac * (1.0 + delta[w])
            if w != s:
                bc[w] += delta[w]

    # Normalize: for undirected, each pair counted twice
    denom = (k - 1) * (k - 2) / 2.0 if k > 2 else 1.0
    # But Brandes sums over all sources, so each pair (s,t) with s!=t
    # is counted once from source s. For undirected divide by 2.
    for i in range(k):
        bc[i] = bc[i] / (2.0 * denom) if denom > 0 else 0.0

    return {i: bc[i] for i in range(k)}


def _closeness_centrality(adj):
    """Closeness centrality: 1 / mean(shortest path distance).

    Only considers reachable nodes.  Returns 0.0 for isolated nodes.
    """
    k = len(adj)
    result = {}
    for i in range(k):
        dists = _bfs_distances(adj, i)
        reachable = [d for j, d in enumerate(dists) if j != i and d > 0]
        if reachable:
            mean_dist = sum(reachable) / len(reachable)
            result[i] = 1.0 / mean_dist if mean_dist > 0 else 0.0
        else:
            result[i] = 0.0
    return result


# ---------- Community detection (greedy modularity) ----------

def _modularity(adj, communities):
    """Compute Newman modularity Q.

    Q = sum_c [ e_cc - a_c^2 ]
    where e_cc = fraction of edges within community c,
          a_c  = fraction of edge-endpoints in community c.
    """
    k = len(adj)
    total_edges = 0
    for i in range(k):
        for j in range(i + 1, k):
            if adj[i][j]:
                total_edges += 1

    if total_edges == 0:
        return 0.0

    # Map node -> community index
    node_comm = {}
    for ci, comm in enumerate(communities):
        for node in comm:
            node_comm[node] = ci

    n_comm = len(communities)
    e = [[0] * n_comm for _ in range(n_comm)]
    for i in range(k):
        for j in range(i + 1, k):
            if adj[i][j]:
                ci = node_comm.get(i, 0)
                cj = node_comm.get(j, 0)
                e[ci][cj] += 1
                e[cj][ci] += 1

    Q = 0.0
    for c in range(n_comm):
        e_cc = e[c][c] / total_edges if total_edges > 0 else 0.0
        a_c = sum(e[c]) / (2.0 * total_edges) if total_edges > 0 else 0.0
        Q += e_cc - a_c * a_c

    return Q


def _greedy_modularity(adj):
    """Greedy agglomerative community detection.

    Start with each node as its own community.  Repeatedly merge
    the pair of communities that gives the greatest increase in Q.
    Stop when no merge improves Q.
    """
    k = len(adj)
    if k == 0:
        return [], 0.0

    # Start: each node is its own community
    communities = [[i] for i in range(k)]
    best_Q = _modularity(adj, communities)

    improved = True
    while improved and len(communities) > 1:
        improved = False
        best_merge = None
        best_new_Q = best_Q

        for i in range(len(communities)):
            for j in range(i + 1, len(communities)):
                trial = [c for idx, c in enumerate(communities)
                         if idx != i and idx != j]
                trial.append(communities[i] + communities[j])
                q = _modularity(adj, trial)
                if q > best_new_Q + 1e-12:
                    best_new_Q = q
                    best_merge = (i, j)

        if best_merge is not None:
            i, j = best_merge
            merged = communities[i] + communities[j]
            communities = [c for idx, c in enumerate(communities)
                           if idx != i and idx != j]
            communities.append(merged)
            best_Q = best_new_Q
            improved = True

    return communities, best_Q


# ---------- Public API ----------

def analyse_theme_network(themes, study_ids=None):
    """Build and analyse a theme co-occurrence network.

    Args:
        themes: list of Theme (with assigned_studies populated).
        study_ids: optional set of study IDs to filter by.

    Returns:
        dict with keys:
            co_occurrence_matrix: list of lists (k × k ints)
            degree_centrality: dict {theme_id: float}
            betweenness_centrality: dict {theme_id: float}
            closeness_centrality: dict {theme_id: float}
            bridging_themes: list of theme_id strings
            communities: list of lists of theme_id strings
            modularity_score: float
    """
    k = len(themes)
    if k == 0:
        return {
            "co_occurrence_matrix": [],
            "degree_centrality": {},
            "betweenness_centrality": {},
            "closeness_centrality": {},
            "bridging_themes": [],
            "communities": [],
            "modularity_score": 0.0,
        }

    cooc, theme_ids = _build_cooccurrence(themes, study_ids)

    # Binary adjacency (off-diagonal co-occurrence > 0)
    adj = [[0] * k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            if i != j and cooc[i][j] > 0:
                adj[i][j] = 1

    deg = _degree_centrality(adj)
    betw = _betweenness_centrality(adj)
    close = _closeness_centrality(adj)

    # Bridging themes: high betweenness (above median) but low degree
    # (below median)
    if k > 0:
        deg_vals = sorted(deg.values())
        betw_vals = sorted(betw.values())
        deg_median = deg_vals[len(deg_vals) // 2]
        betw_median = betw_vals[len(betw_vals) // 2]

        bridging = []
        for i in range(k):
            if betw[i] > betw_median and deg[i] <= deg_median:
                bridging.append(theme_ids[i])
    else:
        bridging = []

    communities_idx, mod_score = _greedy_modularity(adj)

    # Convert index-based results to theme_id-based
    deg_dict = {theme_ids[i]: deg[i] for i in range(k)}
    betw_dict = {theme_ids[i]: betw[i] for i in range(k)}
    close_dict = {theme_ids[i]: close[i] for i in range(k)}
    comm_ids = [[theme_ids[i] for i in comm] for comm in communities_idx]

    return {
        "co_occurrence_matrix": cooc,
        "degree_centrality": deg_dict,
        "betweenness_centrality": betw_dict,
        "closeness_centrality": close_dict,
        "bridging_themes": bridging,
        "communities": comm_ids,
        "modularity_score": mod_score,
    }
