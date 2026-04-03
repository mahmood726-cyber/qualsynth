"""TF-IDF Cosine Similarity for automated theme suggestion.

Pure Python implementation (no numpy/scipy). Builds a TF-IDF
representation of each study's textual content (key_findings + quotes),
computes pairwise cosine similarity, and suggests theme clusters.
"""

import math
import re

# ~100 common English stopwords
STOPWORDS = frozenset([
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "as", "at", "be", "because", "been", "before",
    "being", "below", "between", "both", "but", "by", "can", "could", "did",
    "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "get", "got", "had", "has", "have", "having", "he", "her",
    "here", "hers", "herself", "him", "himself", "his", "how", "i", "if",
    "in", "into", "is", "it", "its", "itself", "just", "me", "might",
    "more", "most", "must", "my", "myself", "no", "nor", "not", "now", "of",
    "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves",
    "out", "over", "own", "s", "same", "she", "should", "so", "some",
    "such", "t", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "we",
    "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "would", "you", "your", "yours", "yourself",
    "yourselves",
])


def _tokenize(text):
    """Lowercase, split on non-alpha, remove stopwords and single chars."""
    tokens = re.split(r"[^a-zA-Z]+", text.lower())
    return [t for t in tokens if t and len(t) > 1 and t not in STOPWORDS]


def _study_text(study):
    """Concatenate key_findings and quote texts for a study."""
    parts = list(study.key_findings)
    for q in study.quotes:
        parts.append(q.text)
    return " ".join(parts)


def _build_vocabulary(studies):
    """Build token lists per study and a global vocabulary set."""
    doc_tokens = []
    vocab = set()
    for s in studies:
        tokens = _tokenize(_study_text(s))
        doc_tokens.append(tokens)
        vocab.update(tokens)
    return doc_tokens, sorted(vocab)


def _term_freq(tokens):
    """Count term frequencies in a token list."""
    freq = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    return freq


def compute_tfidf(studies):
    """Compute TF-IDF vectors for each study.

    Returns:
        doc_vectors: list of dicts {term: tfidf_weight}
        vocabulary: sorted list of all terms
    """
    doc_tokens, vocabulary = _build_vocabulary(studies)
    n_docs = len(studies)

    # Document frequency
    df = {}
    for tokens in doc_tokens:
        seen = set(tokens)
        for t in seen:
            df[t] = df.get(t, 0) + 1

    # IDF: log(N / (1 + df(t)))
    idf = {}
    for t in vocabulary:
        idf[t] = math.log(n_docs / (1 + df.get(t, 0)))

    # TF-IDF per document
    doc_vectors = []
    for tokens in doc_tokens:
        n_tokens = len(tokens)
        if n_tokens == 0:
            doc_vectors.append({})
            continue
        tf = _term_freq(tokens)
        vec = {}
        for t, count in tf.items():
            vec[t] = (count / n_tokens) * idf.get(t, 0.0)
        doc_vectors.append(vec)

    return doc_vectors, vocabulary


def cosine_similarity(vec_a, vec_b):
    """Cosine similarity between two sparse vectors (dicts).

    Returns a value in [0, 1] (non-negative because TF-IDF >= 0).
    """
    # Shared keys for dot product
    common = set(vec_a) & set(vec_b)
    if not common:
        return 0.0

    dot = sum(vec_a[k] * vec_b[k] for k in common)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def build_similarity_matrix(studies):
    """Build pairwise cosine similarity matrix.

    Returns:
        matrix: list of lists (n_studies x n_studies), values in [0, 1].
    """
    doc_vectors, _ = compute_tfidf(studies)
    n = len(studies)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        matrix[i][i] = 1.0
        for j in range(i + 1, n):
            sim = cosine_similarity(doc_vectors[i], doc_vectors[j])
            matrix[i][j] = sim
            matrix[j][i] = sim
    return matrix


def suggest_theme_clusters(studies, threshold=0.3):
    """Suggest theme clusters by grouping studies with similarity > threshold.

    Uses a simple single-linkage approach: start with each study as its own
    cluster, then merge clusters that have any pair above threshold.

    Returns:
        similarity_matrix: list of lists
        suggested_clusters: list of study_id lists
        cluster_labels: list of top-3 term lists per cluster
    """
    matrix = build_similarity_matrix(studies)
    doc_vectors, _ = compute_tfidf(studies)
    n = len(studies)

    # Union-find for clustering
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(n):
        for j in range(i + 1, n):
            if matrix[i][j] > threshold:
                union(i, j)

    # Collect clusters
    clusters_map = {}
    for i in range(n):
        root = find(i)
        if root not in clusters_map:
            clusters_map[root] = []
        clusters_map[root].append(i)

    suggested_clusters = []
    cluster_labels = []

    for indices in clusters_map.values():
        study_ids = [studies[i].study_id for i in indices]
        suggested_clusters.append(study_ids)

        # Aggregate TF-IDF to find top terms for this cluster
        agg = {}
        for i in indices:
            for term, weight in doc_vectors[i].items():
                agg[term] = agg.get(term, 0.0) + weight
        top_terms = sorted(agg.items(), key=lambda x: x[1], reverse=True)
        cluster_labels.append([t[0] for t in top_terms[:3]])

    return matrix, suggested_clusters, cluster_labels
