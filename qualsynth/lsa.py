"""Latent Semantic Analysis via pure-Python SVD (power iteration).

Dimensionality reduction of the term-document matrix to discover
latent concepts, compute semantic similarity, and report variance
explained.  No numpy/scipy — uses only the math module.
"""

import math

from qualsynth.similarity import (
    _tokenize,
    _study_text,
    _build_vocabulary,
    _term_freq,
    compute_tfidf,
)


# ---------- linear-algebra helpers ----------

def _dot(a, b):
    """Dot product of two equal-length lists."""
    return sum(ai * bi for ai, bi in zip(a, b))


def _norm(v):
    """Euclidean norm of a list-vector."""
    return math.sqrt(sum(x * x for x in v))


def _scale(v, s):
    """Multiply vector by scalar."""
    return [x * s for x in v]


def _subtract(a, b):
    """Element-wise a - b."""
    return [ai - bi for ai, bi in zip(a, b)]


def _mat_vec(M, v):
    """Matrix-vector product.  M is list-of-rows, v is a list."""
    return [_dot(row, v) for row in M]


def _transpose(M):
    """Transpose a list-of-rows matrix."""
    if not M:
        return []
    rows, cols = len(M), len(M[0])
    return [[M[r][c] for r in range(rows)] for c in range(cols)]


def _outer(u, v):
    """Outer product of two vectors → matrix (list-of-rows)."""
    return [[ui * vj for vj in v] for ui in u]


# ---------- TF-IDF dense matrix ----------

def _build_tfidf_matrix(studies):
    """Build dense term-document TF-IDF matrix.

    Returns:
        A: list-of-rows  (n_terms × n_docs)
        vocab: sorted vocabulary list
        doc_ids: list of study_id strings
    """
    doc_vectors, vocab = compute_tfidf(studies)
    n_docs = len(studies)
    n_terms = len(vocab)
    term_idx = {t: i for i, t in enumerate(vocab)}

    A = [[0.0] * n_docs for _ in range(n_terms)]
    for j, vec in enumerate(doc_vectors):
        for term, w in vec.items():
            i = term_idx.get(term)
            if i is not None:
                A[i][j] = w

    doc_ids = [s.study_id for s in studies]
    return A, vocab, doc_ids


# ---------- Power-iteration SVD ----------

def _ata(A):
    """Compute A^T A  (k×k where k = n_docs)."""
    AT = _transpose(A)
    k = len(AT)
    result = [[0.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(i, k):
            val = _dot(AT[i], AT[j])
            result[i][j] = val
            result[j][i] = val
    return result


def _power_iteration(M, n_iter=100):
    """Find dominant eigenvector of symmetric M via power iteration.

    Returns (eigenvector, eigenvalue).
    """
    k = len(M)
    # Initial vector: [1, 0.1, 0.01, ...] to break symmetry
    v = [1.0 / (i + 1) for i in range(k)]
    nv = _norm(v)
    if nv > 0:
        v = _scale(v, 1.0 / nv)

    eigenvalue = 0.0
    for _ in range(n_iter):
        w = _mat_vec(M, v)
        eigenvalue = _dot(v, w)
        nw = _norm(w)
        if nw < 1e-15:
            break
        v = _scale(w, 1.0 / nw)

    return v, eigenvalue


def _deflate(M, eigvec, eigval):
    """Subtract eigval * eigvec ⊗ eigvec from M (in-place copy)."""
    k = len(M)
    outer = _outer(eigvec, eigvec)
    return [
        [M[i][j] - eigval * outer[i][j] for j in range(k)]
        for i in range(k)
    ]


def _svd_power(A, r):
    """Truncated SVD via power iteration with deflation.

    Returns:
        U:  n_terms × r  (left singular vectors)
        S:  list of r singular values
        Vt: r × n_docs   (right singular vectors, transposed)
    """
    M = _ata(A)  # k × k
    k = len(M)

    V = []  # columns of V (right singular vectors)
    S = []

    for _ in range(r):
        v, eigval = _power_iteration(M)
        if eigval < 1e-15:
            break
        sigma = math.sqrt(max(eigval, 0.0))
        S.append(sigma)
        V.append(v)
        M = _deflate(M, v, eigval)

    # Compute U = A V Sigma^{-1}
    actual_r = len(S)
    # A is n_terms × k, v is length k
    U = []
    for c in range(actual_r):
        u_col = _mat_vec(A, V[c])
        if S[c] > 1e-15:
            u_col = _scale(u_col, 1.0 / S[c])
        U.append(u_col)

    # U is list of column vectors; convert to n_terms × actual_r matrix
    if actual_r == 0:
        n_terms = len(A)
        U_mat = [[] for _ in range(n_terms)]
    else:
        n_terms = len(U[0])
        U_mat = [[U[c][i] for c in range(actual_r)] for i in range(n_terms)]

    # Vt: actual_r × k
    Vt = [list(V[c]) for c in range(actual_r)]

    return U_mat, S, Vt


# ---------- Public API ----------

def run_lsa(studies, n_concepts=None):
    """Run Latent Semantic Analysis on a set of studies.

    Args:
        studies: list of StudyInput
        n_concepts: number of latent concepts to extract.
                    Default: min(3, n_studies - 1), but at least 1.

    Returns:
        dict with keys:
            concepts: list of {concept_id, top_terms, variance_explained}
            semantic_similarity_matrix: list of lists (n_studies × n_studies)
            total_variance_explained: float in [0, 1]
            n_concepts: int (number actually extracted)
    """
    n = len(studies)
    if n < 2:
        # Degenerate: single study
        return {
            "concepts": [],
            "semantic_similarity_matrix": [[1.0]] if n == 1 else [],
            "total_variance_explained": 0.0,
            "n_concepts": 0,
        }

    if n_concepts is None:
        n_concepts = min(3, n - 1)
    n_concepts = max(1, min(n_concepts, n - 1))

    A, vocab, doc_ids = _build_tfidf_matrix(studies)
    n_terms = len(vocab)

    if n_terms == 0:
        return {
            "concepts": [],
            "semantic_similarity_matrix": [[0.0] * n for _ in range(n)],
            "total_variance_explained": 0.0,
            "n_concepts": 0,
        }

    U, S, Vt = _svd_power(A, n_concepts)

    actual_r = len(S)

    # --- Variance explained ---
    # Total variance = sum of all squared singular values
    # We need the full set; compute from A^T A trace
    ATA_full = _ata(A)
    total_var = sum(ATA_full[i][i] for i in range(len(ATA_full)))
    ss = [s * s for s in S]
    sum_ss = sum(ss)

    concepts = []
    for c in range(actual_r):
        # Top terms by absolute weight in U column c
        term_weights = [(vocab[i], abs(U[i][c])) for i in range(n_terms)]
        term_weights.sort(key=lambda x: x[1], reverse=True)
        top_terms = [tw[0] for tw in term_weights[:5]]

        ve = ss[c] / total_var if total_var > 0 else 0.0
        concepts.append({
            "concept_id": c + 1,
            "top_terms": top_terms,
            "variance_explained": ve,
        })

    total_ve = sum_ss / total_var if total_var > 0 else 0.0

    # --- Semantic similarity in reduced SVD space ---
    # Document representation in SVD space: columns of Vt scaled by S
    # doc_j vector = [S[c] * Vt[c][j] for c in range(actual_r)]
    doc_vecs = []
    for j in range(n):
        vec = [S[c] * Vt[c][j] for c in range(actual_r)]
        doc_vecs.append(vec)

    sim_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        sim_matrix[i][i] = 1.0
        for j in range(i + 1, n):
            d = _dot(doc_vecs[i], doc_vecs[j])
            ni = _norm(doc_vecs[i])
            nj = _norm(doc_vecs[j])
            if ni > 1e-15 and nj > 1e-15:
                cos = d / (ni * nj)
                # Clamp to [0, 1] since TF-IDF values are non-negative
                cos = max(0.0, min(1.0, cos))
            else:
                cos = 0.0
            sim_matrix[i][j] = cos
            sim_matrix[j][i] = cos

    return {
        "concepts": concepts,
        "semantic_similarity_matrix": sim_matrix,
        "total_variance_explained": total_ve,
        "n_concepts": actual_r,
    }
