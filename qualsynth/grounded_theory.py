"""Computational Grounded Theory module.

Pure Python implementation (no numpy/scipy). Formalises the three coding
stages of grounded theory (open, axial, selective), constant comparative
method, and theoretical sampling suggestions.
"""

from qualsynth.similarity import _tokenize


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _study_text(study):
    """Concatenate key_findings and quote texts."""
    parts = list(study.key_findings)
    for q in study.quotes:
        parts.append(q.text)
    return " ".join(parts)


def _extract_ngrams(tokens, n):
    """Extract n-grams from a token list."""
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


# ---------------------------------------------------------------------------
# Open coding
# ---------------------------------------------------------------------------

def _open_coding(studies):
    """Extract codes (frequent bigrams/trigrams) from study key_findings.

    A code is a 2- or 3-word n-gram appearing in >= 2 studies.
    Returns list of {text, frequency, studies}.
    """
    # Per-study ngram sets (to count study-level frequency)
    study_ngrams = {}
    for s in studies:
        tokens = _tokenize(_study_text(s))
        ngrams = set()
        ngrams.update(_extract_ngrams(tokens, 2))
        ngrams.update(_extract_ngrams(tokens, 3))
        study_ngrams[s.study_id] = ngrams

    # Count in how many studies each ngram appears
    ngram_studies = {}
    for sid, ngrams in study_ngrams.items():
        for ng in ngrams:
            if ng not in ngram_studies:
                ngram_studies[ng] = []
            ngram_studies[ng].append(sid)

    # Filter: frequency >= 2
    codes = []
    for ng, sids in sorted(ngram_studies.items()):
        if len(sids) >= 2:
            codes.append({
                "text": ng,
                "frequency": len(sids),
                "studies": sorted(set(sids)),
            })

    # Sort by frequency descending, then alphabetically
    codes.sort(key=lambda c: (-c["frequency"], c["text"]))
    return codes


# ---------------------------------------------------------------------------
# Axial coding
# ---------------------------------------------------------------------------

def _code_cooccurrence(codes):
    """Build code co-occurrence matrix (shared studies).

    Returns:
        matrix: dict of (code_i, code_j) -> int (shared study count)
    """
    matrix = {}
    for i, c1 in enumerate(codes):
        s1 = set(c1["studies"])
        for j, c2 in enumerate(codes):
            if i == j:
                continue
            s2 = set(c2["studies"])
            shared = len(s1 & s2)
            if shared > 0:
                matrix[(c1["text"], c2["text"])] = shared
    return matrix


def _agglomerative_cluster(codes, threshold=0.2):
    """Simple agglomerative clustering of codes based on co-occurrence.

    Merges the most co-occurring pair repeatedly until similarity < threshold.
    Similarity = shared_studies / max(len(studies_a), len(studies_b)).

    Returns list of clusters, each a list of code texts.
    """
    if not codes:
        return []

    # Each code starts as its own cluster
    clusters = [[c["text"]] for c in codes]
    code_studies = {c["text"]: set(c["studies"]) for c in codes}

    def cluster_studies(cluster):
        """Union of all studies for codes in a cluster."""
        result = set()
        for ct in cluster:
            result |= code_studies.get(ct, set())
        return result

    while len(clusters) > 1:
        # Find the pair with highest similarity
        best_sim = -1.0
        best_i, best_j = -1, -1
        for i in range(len(clusters)):
            si = cluster_studies(clusters[i])
            for j in range(i + 1, len(clusters)):
                sj = cluster_studies(clusters[j])
                shared = len(si & sj)
                max_size = max(len(si), len(sj))
                if max_size == 0:
                    continue
                sim = shared / max_size
                if sim > best_sim:
                    best_sim = sim
                    best_i, best_j = i, j

        if best_sim < threshold:
            break

        # Merge best_j into best_i
        clusters[best_i] = clusters[best_i] + clusters[best_j]
        clusters.pop(best_j)

    return clusters


def _axial_coding(codes, studies, threshold=0.2):
    """Group codes into axial categories via agglomerative clustering.

    Returns list of {label, codes, n_studies}.
    """
    clusters = _agglomerative_cluster(codes, threshold)
    code_studies = {c["text"]: set(c["studies"]) for c in codes}

    categories = []
    for i, cluster in enumerate(clusters):
        all_studies = set()
        for ct in cluster:
            all_studies |= code_studies.get(ct, set())
        # Label = most frequent code in cluster
        label = cluster[0]  # already sorted by frequency in open coding
        categories.append({
            "label": label,
            "codes": sorted(cluster),
            "n_studies": len(all_studies),
        })

    # Sort by n_studies descending
    categories.sort(key=lambda c: (-c["n_studies"], c["label"]))
    return categories


# ---------------------------------------------------------------------------
# Selective coding
# ---------------------------------------------------------------------------

def _selective_coding(categories):
    """Identify the core category.

    Score = 0.5*centrality + 0.3*connectivity + 0.2*frequency
    All normalised to [0, 1].
    """
    if not categories:
        return ""

    n_cat = len(categories)
    if n_cat == 1:
        return categories[0]["label"]

    # Build category co-occurrence network
    cat_studies = {}
    for cat in categories:
        all_studies = set()
        # Recompute from codes would need original codes; use n_studies as proxy
        # Actually we need the actual study sets. Store them.
        cat_studies[cat["label"]] = cat  # categories already have n_studies

    # For connectivity: count how many other categories share studies
    # We need study sets. Reconstruct from codes list.
    # Since we don't have study sets here, we'll compute connectivity from
    # the category labels and n_studies. A simpler approach: use the codes
    # to determine which categories overlap.

    # Actually, let's compute proper study sets
    # We can't easily do that here without codes + their studies.
    # So we compute within run_grounded_theory and pass study sets in.

    # Fallback: use n_studies as the frequency metric, and for centrality
    # and connectivity, we approximate using the number of codes.
    max_studies = max(c["n_studies"] for c in categories)
    max_codes = max(len(c["codes"]) for c in categories)

    best_label = ""
    best_score = -1.0
    for cat in categories:
        freq_norm = cat["n_studies"] / max_studies if max_studies > 0 else 0
        code_norm = len(cat["codes"]) / max_codes if max_codes > 0 else 0
        # Approximate centrality as fraction of total categories that this one
        # could connect to (proxy: n_studies overlap potential)
        centrality_norm = freq_norm  # proxy
        connectivity_norm = code_norm

        score = 0.5 * centrality_norm + 0.3 * connectivity_norm + 0.2 * freq_norm
        if score > best_score:
            best_score = score
            best_label = cat["label"]

    return best_label


def _selective_coding_with_studies(categories, cat_study_sets):
    """Identify core category using actual study set overlaps.

    Score = 0.5*centrality + 0.3*connectivity + 0.2*frequency
    All normalised to [0, 1].
    """
    if not categories:
        return ""
    if len(categories) == 1:
        return categories[0]["label"]

    n_cat = len(categories)
    labels = [c["label"] for c in categories]

    # Degree centrality: fraction of other categories with shared studies
    degree = {}
    for i, a in enumerate(labels):
        connections = 0
        for j, b in enumerate(labels):
            if i == j:
                continue
            if cat_study_sets.get(a, set()) & cat_study_sets.get(b, set()):
                connections += 1
        degree[a] = connections / (n_cat - 1) if n_cat > 1 else 0

    # Connectivity: number of connected categories
    connectivity = {}
    max_conn = max(degree.values()) if degree else 1
    for lab in labels:
        connectivity[lab] = degree[lab] / max_conn if max_conn > 0 else 0

    # Frequency: total study count normalised
    freqs = {c["label"]: c["n_studies"] for c in categories}
    max_freq = max(freqs.values()) if freqs else 1
    freq_norm = {lab: freqs[lab] / max_freq if max_freq > 0 else 0 for lab in labels}

    best_label = ""
    best_score = -1.0
    for lab in labels:
        score = 0.5 * degree.get(lab, 0) + 0.3 * connectivity.get(lab, 0) + 0.2 * freq_norm.get(lab, 0)
        if score > best_score:
            best_score = score
            best_label = lab

    return best_label


# ---------------------------------------------------------------------------
# Theoretical sampling
# ---------------------------------------------------------------------------

def _theoretical_sampling(categories, total_studies):
    """Suggest which categories need more data.

    Categories with lowest coverage (n_studies / total) are suggested.
    """
    if not categories or total_studies == 0:
        return []

    suggestions = []
    for cat in categories:
        coverage = cat["n_studies"] / total_studies
        if coverage < 0.5:
            suggestions.append(
                f"Seek studies about '{cat['label']}' "
                f"(current coverage: {cat['n_studies']}/{total_studies} studies)"
            )

    # Sort by coverage ascending (lowest first)
    suggestions.sort()
    return suggestions


# ---------------------------------------------------------------------------
# Constant comparative method
# ---------------------------------------------------------------------------

def _constant_comparative(themes):
    """Pairwise comparison matrix of themes.

    For each pair compute: overlap (shared studies), divergence (unique studies),
    similarity (Jaccard). Flag high-similarity pairs (>0.7) for merge,
    zero-overlap pairs for maximal contrast.
    """
    comparison_matrix = {}
    merge_candidates = []
    contrast_pairs = []

    for i, t1 in enumerate(themes):
        s1 = set(t1.assigned_studies)
        for j, t2 in enumerate(themes):
            if i >= j:
                continue
            s2 = set(t2.assigned_studies)
            overlap = len(s1 & s2)
            divergence = len(s1 ^ s2)  # symmetric difference
            union = len(s1 | s2)
            jaccard = overlap / union if union > 0 else 0.0

            key = (t1.theme_id, t2.theme_id)
            comparison_matrix[key] = {
                "overlap": overlap,
                "divergence": divergence,
                "similarity": jaccard,
            }

            if jaccard > 0.7:
                merge_candidates.append({
                    "theme_a": t1.theme_id,
                    "theme_b": t2.theme_id,
                    "similarity": jaccard,
                })
            if overlap == 0 and len(s1) > 0 and len(s2) > 0:
                contrast_pairs.append({
                    "theme_a": t1.theme_id,
                    "theme_b": t2.theme_id,
                })

    return comparison_matrix, merge_candidates, contrast_pairs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_grounded_theory(studies, themes):
    """Run computational grounded theory analysis.

    Args:
        studies: list of StudyInput
        themes: list of Theme (used for constant comparative method)

    Returns:
        dict with keys:
            open_codes: list of {text, frequency, studies}
            axial_categories: list of {label, codes, n_studies}
            core_category: str
            theoretical_sampling: list of suggestion strings
            comparison_matrix: dict of (theme_a, theme_b) -> {overlap, divergence, similarity}
            merge_candidates: list of {theme_a, theme_b, similarity}
            contrast_pairs: list of {theme_a, theme_b}
    """
    # Open coding
    codes = _open_coding(studies)

    # Axial coding
    categories = _axial_coding(codes, studies, threshold=0.2)

    # Build study sets for selective coding
    code_studies_map = {c["text"]: set(c["studies"]) for c in codes}
    cat_study_sets = {}
    for cat in categories:
        all_studies = set()
        for ct in cat["codes"]:
            all_studies |= code_studies_map.get(ct, set())
        cat_study_sets[cat["label"]] = all_studies

    # Selective coding
    core = _selective_coding_with_studies(categories, cat_study_sets)

    # Theoretical sampling
    sampling = _theoretical_sampling(categories, len(studies))

    # Constant comparative method
    comparison_matrix, merge_candidates, contrast_pairs = _constant_comparative(themes)

    return {
        "open_codes": codes,
        "axial_categories": categories,
        "core_category": core,
        "theoretical_sampling": sampling,
        "comparison_matrix": comparison_matrix,
        "merge_candidates": merge_candidates,
        "contrast_pairs": contrast_pairs,
    }
