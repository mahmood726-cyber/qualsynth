"""Graph Kernel Similarity for Qualitative Studies.

Pure Python implementation. Builds per-study subgraphs of theme
co-occurrence, computes Weisfeiler-Leman (WL) and random walk kernels,
performs kernel PCA for 2D embedding, and normalised similarity.
"""

import math


def _build_study_subgraph(study, themes):
    """Build a subgraph for a study: nodes = themes it belongs to,
    edges = co-occurrence between those themes (both share this study).

    Returns:
        nodes: list of theme_ids
        adj: dict {(ti, tj): 1} for edges (undirected)
        labels: dict {theme_id: label}
    """
    # Themes that include this study
    study_themes = []
    for t in themes:
        if study.study_id in t.assigned_studies:
            study_themes.append(t)

    nodes = [t.theme_id for t in study_themes]
    labels = {t.theme_id: t.label for t in study_themes}
    adj = {}

    for i, ti in enumerate(study_themes):
        for j, tj in enumerate(study_themes):
            if i < j:
                # Edge if both themes share this study (they do by construction)
                adj[(ti.theme_id, tj.theme_id)] = 1
                adj[(tj.theme_id, ti.theme_id)] = 1

    return nodes, adj, labels


def _wl_hash(label, neighbor_labels):
    """Deterministic hash for WL relabeling."""
    sorted_neighbors = tuple(sorted(neighbor_labels))
    return hash((label, sorted_neighbors))


def _wl_histogram(nodes, adj, labels, h_iterations=3):
    """Compute WL histogram for a graph after h iterations.

    Returns:
        histogram: dict {label_hash: count}
    """
    current_labels = dict(labels)
    histogram = {}

    # Iteration 0: count initial labels
    for n in nodes:
        lbl = current_labels.get(n, "")
        h = hash(lbl)
        histogram[h] = histogram.get(h, 0) + 1

    for iteration in range(h_iterations):
        new_labels = {}
        for n in nodes:
            neighbors = []
            for m in nodes:
                if m != n and (n, m) in adj:
                    neighbors.append(str(current_labels.get(m, "")))
            new_label = _wl_hash(str(current_labels.get(n, "")), neighbors)
            new_labels[n] = new_label

        current_labels = new_labels
        for n in nodes:
            h = current_labels[n]
            histogram[h] = histogram.get(h, 0) + 1

    return histogram


def _wl_kernel_value(hist_a, hist_b):
    """Dot product of two WL histograms."""
    common = set(hist_a) & set(hist_b)
    return sum(hist_a[k] * hist_b[k] for k in common)


def _count_walks(nodes, adj, length):
    """Count number of walks of a given length in a graph.

    For length 0: number of nodes.
    For length l: sum over all paths of length l.

    Returns adjacency matrix power trace approach:
    Represent adj as matrix, compute A^l, return sum of all entries.
    """
    n = len(nodes)
    if n == 0:
        return 0

    node_idx = {nid: i for i, nid in enumerate(nodes)}

    # Build adjacency matrix
    A = [[0] * n for _ in range(n)]
    for i, ni in enumerate(nodes):
        for j, nj in enumerate(nodes):
            if i != j and (ni, nj) in adj:
                A[i][j] = 1

    # Compute A^length
    if length == 0:
        return n

    result = [row[:] for row in A]
    for _ in range(length - 1):
        new = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                s = 0
                for k in range(n):
                    s += result[i][k] * A[k][j]
                new[i][j] = s
        result = new

    return sum(result[i][j] for i in range(n) for j in range(n))


def _common_walks(nodes_a, adj_a, nodes_b, adj_b, length):
    """Count common walks of given length between two graphs.

    Uses direct product graph approach:
    Nodes of product: (a, b) for a in A, b in B
    Edge ((a1,b1), (a2,b2)) if (a1,a2) in A and (b1,b2) in B
    Common walks = number of walks of given length in product graph.
    """
    if not nodes_a or not nodes_b:
        return 0

    # Product graph nodes
    prod_nodes = []
    for a in nodes_a:
        for b in nodes_b:
            prod_nodes.append((a, b))

    if not prod_nodes:
        return 0

    if length == 0:
        return len(prod_nodes)

    n = len(prod_nodes)
    idx = {node: i for i, node in enumerate(prod_nodes)}

    # Product adjacency
    A = [[0] * n for _ in range(n)]
    for i, (a1, b1) in enumerate(prod_nodes):
        for j, (a2, b2) in enumerate(prod_nodes):
            if i != j and (a1, a2) in adj_a and (b1, b2) in adj_b:
                A[i][j] = 1

    # Compute A^length
    result = [row[:] for row in A]
    for _ in range(length - 1):
        new_mat = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                s = 0
                for k in range(n):
                    s += result[i][k] * A[k][j]
                new_mat[i][j] = s
        result = new_mat

    return sum(result[i][j] for i in range(n) for j in range(n))


def _rw_kernel_value(nodes_a, adj_a, nodes_b, adj_b, lam=0.1, max_l=3):
    """Random walk kernel: K_rw = sum_{l=1}^{max_l} lambda^l * n_common_walks(l)."""
    total = 0.0
    for l in range(1, max_l + 1):
        cw = _common_walks(nodes_a, adj_a, nodes_b, adj_b, l)
        total += (lam ** l) * cw
    return total


def _center_kernel(K, n):
    """Center a kernel matrix: K_c = K - 1_n K - K 1_n + 1_n K 1_n."""
    row_means = [sum(K[i]) / n for i in range(n)]
    col_means = [sum(K[i][j] for i in range(n)) / n for j in range(n)]
    total_mean = sum(row_means) / n

    Kc = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            Kc[i][j] = K[i][j] - row_means[i] - col_means[j] + total_mean
    return Kc


def _eigen_decompose_2x2_symmetric(a, b, d):
    """Eigenvalues/vectors of [[a, b], [b, d]] symmetric 2x2."""
    trace = a + d
    det = a * d - b * b
    disc = trace * trace - 4 * det
    if disc < 0:
        disc = 0.0
    sqrt_disc = math.sqrt(disc)
    l1 = (trace + sqrt_disc) / 2.0
    l2 = (trace - sqrt_disc) / 2.0
    return l1, l2


def _kernel_pca(K, n, n_components=2):
    """Kernel PCA: eigendecompose centered kernel, project to top components.

    Simple power iteration for top eigenvectors of a symmetric matrix.
    Returns list of (eigenvalue, eigenvector) pairs.
    """
    Kc = _center_kernel(K, n)

    if n == 0:
        return []

    # Power iteration for top eigenvectors
    results = []
    # Work on a copy for deflation
    M = [row[:] for row in Kc]

    for comp in range(min(n_components, n)):
        # Initialize with a deterministic vector
        v = [1.0 / math.sqrt(n)] * n
        # Slightly perturb to break symmetry
        for i in range(n):
            v[i] += (i + 1) * 1e-8

        # Normalize
        norm = math.sqrt(sum(x * x for x in v))
        if norm > 0:
            v = [x / norm for x in v]

        for iteration in range(200):
            # Matrix-vector multiply
            new_v = [0.0] * n
            for i in range(n):
                s = 0.0
                for j in range(n):
                    s += M[i][j] * v[j]
                new_v[i] = s

            # Compute eigenvalue (Rayleigh quotient)
            eigenvalue = sum(new_v[i] * v[i] for i in range(n))

            # Normalize
            norm = math.sqrt(sum(x * x for x in new_v))
            if norm < 1e-15:
                break
            new_v = [x / norm for x in new_v]

            # Check convergence
            diff = sum((new_v[i] - v[i]) ** 2 for i in range(n))
            v = new_v
            if diff < 1e-12:
                break

        eigenvalue = sum(v[i] * sum(M[i][j] * v[j] for j in range(n)) for i in range(n))
        results.append((max(eigenvalue, 0.0), v))

        # Deflate
        for i in range(n):
            for j in range(n):
                M[i][j] -= eigenvalue * v[i] * v[j]

    return results


def analyse_graph_kernels(studies, themes):
    """Graph kernel analysis of study similarity.

    Args:
        studies: list of StudyInput
        themes: list of Theme (with assigned_studies)

    Returns:
        dict with keys:
            wl_kernel_matrix: list of lists (n x n)
            rw_kernel_matrix: list of lists (n x n)
            kernel_pca_coords: dict {study_id: [x, y]}
            normalized_similarity: list of lists (n x n)
    """
    n = len(studies)
    if n == 0:
        return {
            "wl_kernel_matrix": [],
            "rw_kernel_matrix": [],
            "kernel_pca_coords": {},
            "normalized_similarity": [],
        }

    # Build subgraphs per study
    subgraphs = []
    for s in studies:
        nodes, adj, labels = _build_study_subgraph(s, themes)
        subgraphs.append((nodes, adj, labels))

    # WL kernel matrix
    histograms = []
    for nodes, adj, labels in subgraphs:
        hist = _wl_histogram(nodes, adj, labels, h_iterations=3)
        histograms.append(hist)

    wl_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            val = _wl_kernel_value(histograms[i], histograms[j])
            wl_matrix[i][j] = float(val)
            wl_matrix[j][i] = float(val)

    # Random walk kernel matrix
    rw_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            nodes_a, adj_a, _ = subgraphs[i]
            nodes_b, adj_b, _ = subgraphs[j]
            val = _rw_kernel_value(nodes_a, adj_a, nodes_b, adj_b,
                                   lam=0.1, max_l=3)
            rw_matrix[i][j] = val
            rw_matrix[j][i] = val

    # Normalized similarity from WL kernel: K_ij / sqrt(K_ii * K_jj)
    normalized = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            denom = math.sqrt(wl_matrix[i][i] * wl_matrix[j][j])
            if denom > 0:
                normalized[i][j] = wl_matrix[i][j] / denom
            else:
                normalized[i][j] = 0.0

    # Kernel PCA on WL kernel
    eigen_results = _kernel_pca(wl_matrix, n, n_components=2)

    pca_coords = {}
    for idx, s in enumerate(studies):
        coords = []
        for eigenvalue, eigvec in eigen_results:
            scale = math.sqrt(eigenvalue) if eigenvalue > 0 else 0.0
            coords.append(eigvec[idx] * scale)
        while len(coords) < 2:
            coords.append(0.0)
        pca_coords[s.study_id] = coords[:2]

    return {
        "wl_kernel_matrix": wl_matrix,
        "rw_kernel_matrix": rw_matrix,
        "kernel_pca_coords": pca_coords,
        "normalized_similarity": normalized,
    }
