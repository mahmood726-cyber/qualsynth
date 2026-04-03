"""Word Embeddings via Co-occurrence Matrix SVD.

Simple distributional semantics using co-occurrence counts,
PPMI transformation, and power-iteration SVD to produce
d-dimensional word vectors.  Pure Python (no numpy/scipy).

Reuses _tokenize from similarity.py and SVD helpers from lsa.py.
"""

import math

from qualsynth.similarity import _tokenize, _study_text
from qualsynth.lsa import (
    _dot,
    _norm,
    _scale,
    _transpose,
    _svd_power,
)


# ---------- Co-occurrence matrix ----------

def _collect_documents(studies):
    """Return list of token-lists from key_findings + quotes."""
    docs = []
    for s in studies:
        tokens = _tokenize(_study_text(s))
        docs.append(tokens)
    return docs


def _build_vocabulary_filtered(docs, min_docs=2):
    """Build vocabulary of words appearing in >= min_docs documents."""
    doc_freq = {}
    for tokens in docs:
        seen = set(tokens)
        for w in seen:
            doc_freq[w] = doc_freq.get(w, 0) + 1
    vocab = sorted(w for w, df in doc_freq.items() if df >= min_docs)
    return vocab


def _build_cooccurrence_matrix(docs, vocab, window=5):
    """Build symmetric word co-occurrence matrix from documents.

    For each document, for every pair of words within a sliding
    window of the given size, increment the co-occurrence count.

    Returns:
        cooc: list-of-lists (V x V) of counts
        word_counts: dict word -> total occurrences across all docs
        total_pairs: total number of co-occurrence pair increments
    """
    word_idx = {w: i for i, w in enumerate(vocab)}
    V = len(vocab)
    cooc = [[0] * V for _ in range(V)]
    word_counts = {w: 0 for w in vocab}

    total_pairs = 0

    for tokens in docs:
        # Filter to vocab words only, but keep positions
        filtered = [(i, t) for i, t in enumerate(tokens) if t in word_idx]
        for pos_a in range(len(filtered)):
            idx_a, w_a = filtered[pos_a]
            word_counts[w_a] = word_counts.get(w_a, 0) + 1
            for pos_b in range(pos_a + 1, len(filtered)):
                idx_b, w_b = filtered[pos_b]
                if idx_b - idx_a > window:
                    break
                i_a = word_idx[w_a]
                i_b = word_idx[w_b]
                cooc[i_a][i_b] += 1
                cooc[i_b][i_a] += 1
                total_pairs += 1

    return cooc, word_counts, total_pairs


# ---------- PPMI ----------

def _ppmi_transform(cooc, word_counts, vocab, total_pairs):
    """Positive Pointwise Mutual Information transformation.

    PMI(w1, w2) = log2(P(w1,w2) / (P(w1) * P(w2)))
    PPMI = max(0, PMI)

    Returns:
        ppmi: list-of-lists (V x V) of floats
    """
    V = len(vocab)
    total_words = sum(word_counts.values())

    if total_pairs == 0 or total_words == 0:
        return [[0.0] * V for _ in range(V)]

    ppmi = [[0.0] * V for _ in range(V)]

    for i in range(V):
        p_w1 = word_counts[vocab[i]] / total_words
        if p_w1 == 0:
            continue
        for j in range(i + 1, V):
            if cooc[i][j] == 0:
                continue
            p_w2 = word_counts[vocab[j]] / total_words
            if p_w2 == 0:
                continue
            p_pair = cooc[i][j] / total_pairs
            pmi = math.log2(p_pair / (p_w1 * p_w2))
            val = max(0.0, pmi)
            ppmi[i][j] = val
            ppmi[j][i] = val

    return ppmi


# ---------- k-means ----------

def _cosine_sim(a, b):
    """Cosine similarity between two list-vectors."""
    d = _dot(a, b)
    na = _norm(a)
    nb = _norm(b)
    if na < 1e-15 or nb < 1e-15:
        return 0.0
    return d / (na * nb)


def _euclidean_dist_sq(a, b):
    """Squared Euclidean distance."""
    return sum((ai - bi) ** 2 for ai, bi in zip(a, b))


def _kmeans(vectors, k, max_iter=20):
    """Simple k-means clustering on list-vectors.

    Uses deterministic init: pick first k vectors as initial centroids
    (sorted by index to be reproducible).

    Returns:
        clusters: list of k lists, each containing word indices
    """
    n = len(vectors)
    if n == 0 or k <= 0:
        return []

    dim = len(vectors[0])

    # Deterministic init: spread across the dataset
    step = max(1, n // k)
    centroids = [list(vectors[min(i * step, n - 1)]) for i in range(k)]

    assignments = [0] * n

    for _ in range(max_iter):
        # Assign each vector to nearest centroid
        new_assignments = [0] * n
        for i in range(n):
            best_c = 0
            best_dist = _euclidean_dist_sq(vectors[i], centroids[0])
            for c in range(1, k):
                d = _euclidean_dist_sq(vectors[i], centroids[c])
                if d < best_dist:
                    best_dist = d
                    best_c = c
            new_assignments[i] = best_c

        # Recompute centroids
        new_centroids = [[0.0] * dim for _ in range(k)]
        counts = [0] * k
        for i in range(n):
            c = new_assignments[i]
            counts[c] += 1
            for d_idx in range(dim):
                new_centroids[c][d_idx] += vectors[i][d_idx]

        for c in range(k):
            if counts[c] > 0:
                for d_idx in range(dim):
                    new_centroids[c][d_idx] /= counts[c]
            else:
                # Keep old centroid for empty clusters
                new_centroids[c] = list(centroids[c])

        # Check convergence
        if new_assignments == assignments:
            assignments = new_assignments
            centroids = new_centroids
            break

        assignments = new_assignments
        centroids = new_centroids

    # Build clusters
    clusters = [[] for _ in range(k)]
    for i in range(n):
        clusters[assignments[i]].append(i)

    # Remove empty clusters
    clusters = [c for c in clusters if len(c) > 0]

    return clusters


# ---------- Public API ----------

def compute_word_embeddings(studies, embedding_dim=10, window=5):
    """Compute word embeddings from study text via co-occurrence SVD.

    Pipeline:
    1. Collect documents (key_findings + quotes) and tokenize
    2. Build vocabulary (words in >= 2 documents)
    3. Build co-occurrence matrix with context window
    4. Apply PPMI transformation
    5. SVD dimensionality reduction to get word vectors
    6. Compute nearest neighbors and concept clusters

    Args:
        studies: list of StudyInput
        embedding_dim: target dimensionality (default 10)
        window: co-occurrence context window size (default 5)

    Returns:
        dict with keys:
            vocabulary: list of words
            word_vectors: dict word -> list of floats (embedding)
            nearest_neighbors: dict word -> list of 5 nearest words
            concept_clusters: list of word lists
            embedding_dim: int (actual dimensionality used)
    """
    docs = _collect_documents(studies)

    vocab = _build_vocabulary_filtered(docs, min_docs=2)

    if len(vocab) == 0:
        return {
            "vocabulary": [],
            "word_vectors": {},
            "nearest_neighbors": {},
            "concept_clusters": [],
            "embedding_dim": 0,
        }

    V = len(vocab)

    # Build co-occurrence and PPMI
    cooc, word_counts, total_pairs = _build_cooccurrence_matrix(
        docs, vocab, window=window
    )
    ppmi = _ppmi_transform(cooc, word_counts, vocab, total_pairs)

    # SVD on PPMI matrix
    # Actual dim: min(embedding_dim, V - 1), at least 1
    actual_dim = max(1, min(embedding_dim, V - 1))

    # _svd_power expects a matrix A (rows x cols) and extracts right
    # singular vectors of A^T A. For a symmetric PPMI matrix (V x V),
    # the SVD gives us the principal components directly.
    U, S, Vt = _svd_power(ppmi, actual_dim)

    # Word vectors: rows of U scaled by sqrt(S) for balanced representation
    word_vectors = {}
    for i in range(V):
        vec = []
        for c in range(len(S)):
            weight = U[i][c] * math.sqrt(max(S[c], 0.0)) if len(U[i]) > c else 0.0
            vec.append(weight)
        # Pad if SVD returned fewer components
        while len(vec) < actual_dim:
            vec.append(0.0)
        word_vectors[vocab[i]] = vec

    # Nearest neighbors: top 5 by cosine similarity
    nearest_neighbors = {}
    for w in vocab:
        sims = []
        vec_w = word_vectors[w]
        for w2 in vocab:
            if w2 == w:
                continue
            sim = _cosine_sim(vec_w, word_vectors[w2])
            sims.append((w2, sim))
        sims.sort(key=lambda x: -x[1])
        nearest_neighbors[w] = [s[0] for s in sims[:5]]

    # Concept clusters via k-means
    k = min(5, max(1, V // 3))
    all_vecs = [word_vectors[w] for w in vocab]
    cluster_indices = _kmeans(all_vecs, k)

    concept_clusters = []
    for cl in cluster_indices:
        concept_clusters.append([vocab[idx] for idx in cl])

    return {
        "vocabulary": vocab,
        "word_vectors": word_vectors,
        "nearest_neighbors": nearest_neighbors,
        "concept_clusters": concept_clusters,
        "embedding_dim": actual_dim,
    }
