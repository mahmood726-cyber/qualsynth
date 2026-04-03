"""Meta-narrative synthesis: competing storylines and paradigmatic positions.

Pure Python implementation (no numpy/scipy). Identifies narrative
traditions by extracting theme-ordering storylines, computing edit
distance similarity, clustering narratives, and detecting paradigm
evolution and bridging themes.
"""


# ---- Levenshtein edit distance (pure DP) ----

def _edit_distance(seq_a, seq_b):
    """Compute Levenshtein edit distance between two sequences.

    Works on any sequence of hashable items (e.g. theme_id strings).
    """
    m, n = len(seq_a), len(seq_b)
    # dp[i][j] = edit distance of seq_a[:i] vs seq_b[:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if seq_a[i - 1] == seq_b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # deletion
                dp[i][j - 1] + 1,      # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )
    return dp[m][n]


def _normalized_similarity(seq_a, seq_b):
    """Normalized similarity: 1 - (edit_distance / max_length), in [0, 1].

    Returns 1.0 if both are empty.
    """
    max_len = max(len(seq_a), len(seq_b))
    if max_len == 0:
        return 1.0
    ed = _edit_distance(seq_a, seq_b)
    return 1.0 - (ed / max_len)


# ---- Narrative extraction ----

def _extract_storyline(study, themes):
    """Extract the storyline for a study: ordered list of theme_ids.

    Themes are ordered by their first mention in the study's key_findings.
    A theme is considered "mentioned" if any of its label words or concept
    words appear in a key_finding.
    """
    # Build theme keyword sets
    theme_keywords = {}
    for t in themes:
        keywords = set()
        for word in t.label.lower().split():
            if len(word) > 2:
                keywords.add(word)
        for concept in t.concepts:
            for word in concept.lower().split():
                if len(word) > 2:
                    keywords.add(word)
        theme_keywords[t.theme_id] = keywords

    # Also check if theme is assigned to this study
    study_themes_assigned = set()
    for t in themes:
        if study.study_id in t.assigned_studies:
            study_themes_assigned.add(t.theme_id)

    # Order by first mention in key_findings
    theme_first_mention = {}
    for idx, finding in enumerate(study.key_findings):
        finding_lower = finding.lower()
        finding_words = set(finding_lower.split())
        for t in themes:
            tid = t.theme_id
            if tid in theme_first_mention:
                continue
            kw = theme_keywords.get(tid, set())
            if kw & finding_words:
                theme_first_mention[tid] = idx

    # Include assigned themes not yet mentioned (append at end)
    next_idx = len(study.key_findings)
    for tid in study_themes_assigned:
        if tid not in theme_first_mention:
            theme_first_mention[tid] = next_idx
            next_idx += 1

    # Sort by first mention order
    storyline = sorted(theme_first_mention.keys(),
                       key=lambda tid: theme_first_mention[tid])
    return storyline


# ---- Single-linkage clustering ----

def _cluster_narratives(study_ids, narratives, similarity_matrix, threshold=0.5):
    """Cluster studies by narrative similarity using single-linkage.

    Returns list of clusters, each a list of study_ids.
    """
    n = len(study_ids)
    # Union-find
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

    id_to_idx = {sid: i for i, sid in enumerate(study_ids)}

    for i in range(n):
        for j in range(i + 1, n):
            si, sj = study_ids[i], study_ids[j]
            sim = similarity_matrix.get((si, sj),
                                        similarity_matrix.get((sj, si), 0.0))
            if sim > threshold:
                union(i, j)

    # Collect clusters
    clusters_map = {}
    for i in range(n):
        root = find(i)
        if root not in clusters_map:
            clusters_map[root] = []
        clusters_map[root].append(study_ids[i])

    return list(clusters_map.values())


# ---- Public API ----

def analyse_meta_narrative(studies, themes):
    """Identify competing storylines and paradigmatic positions.

    Args:
        studies: list of StudyInput
        themes: list of Theme (with assigned_studies and concepts populated)

    Returns:
        dict with keys:
            narratives: dict {study_id: list of theme_ids}
            clusters: list of {studies, core_themes, distinctive_themes}
            narrative_similarity_matrix: dict {(study_a, study_b): float}
            n_traditions: int
            paradigm_evolution: list of {era, dominant_cluster}
            incommensurability_index: float
            bridging_themes: list of theme_ids
    """
    # ---- Extract storylines ----
    narratives = {}
    for s in studies:
        narratives[s.study_id] = _extract_storyline(s, themes)

    study_ids = [s.study_id for s in studies]

    # ---- Narrative similarity matrix ----
    similarity_matrix = {}
    for i, si in enumerate(study_ids):
        for j, sj in enumerate(study_ids):
            if i <= j:
                sim = _normalized_similarity(narratives[si], narratives[sj])
                similarity_matrix[(si, sj)] = sim
                similarity_matrix[(sj, si)] = sim

    # ---- Cluster studies ----
    clusters_raw = _cluster_narratives(
        study_ids, narratives, similarity_matrix, threshold=0.5
    )

    # ---- Paradigm mapping per cluster ----
    all_theme_ids = {t.theme_id for t in themes}
    clusters = []

    # Build theme-to-study counts per cluster
    for cluster_studies in clusters_raw:
        cluster_set = set(cluster_studies)
        theme_counts = {}  # theme_id -> count of studies in cluster that have it
        for sid in cluster_studies:
            for tid in narratives.get(sid, []):
                theme_counts[tid] = theme_counts.get(tid, 0) + 1

        n_cluster = len(cluster_studies)
        # Core themes: appearing in >50% of cluster's studies
        core_themes = [
            tid for tid, cnt in theme_counts.items()
            if cnt > n_cluster * 0.5
        ]
        clusters.append({
            "studies": cluster_studies,
            "core_themes": core_themes,
            "distinctive_themes": [],  # filled below
        })

    # Distinctive themes: in this cluster but not in other clusters' core
    all_core = set()
    for c in clusters:
        all_core.update(c["core_themes"])

    for c in clusters:
        other_core = set()
        for c2 in clusters:
            if c2 is not c:
                other_core.update(c2["core_themes"])
        c["distinctive_themes"] = [
            tid for tid in c["core_themes"]
            if tid not in other_core
        ]

    n_traditions = len(clusters)

    # ---- Paradigm evolution ----
    # Group studies by year, find which cluster dominates each era
    year_map = {}
    study_to_cluster = {}
    for ci, c in enumerate(clusters):
        for sid in c["studies"]:
            study_to_cluster[sid] = ci

    for s in studies:
        yr = s.year
        if yr not in year_map:
            year_map[yr] = []
        year_map[yr].append(study_to_cluster.get(s.study_id, 0))

    paradigm_evolution = []
    for yr in sorted(year_map.keys()):
        cluster_counts = {}
        for ci in year_map[yr]:
            cluster_counts[ci] = cluster_counts.get(ci, 0) + 1
        dominant = max(cluster_counts, key=cluster_counts.get)
        paradigm_evolution.append({
            "era": yr,
            "dominant_cluster": dominant,
        })

    # ---- Incommensurability index ----
    # Proportion of theme pairs that appear in different clusters but
    # never together in the same study
    theme_ids_list = [t.theme_id for t in themes]
    n_theme_pairs = 0
    n_incommensurable = 0

    # Build study -> theme set for co-occurrence check
    study_theme_set = {}
    for sid in study_ids:
        study_theme_set[sid] = set(narratives.get(sid, []))

    # Build theme -> cluster set
    theme_cluster_map = {}  # theme_id -> set of cluster indices
    for ci, c in enumerate(clusters):
        for sid in c["studies"]:
            for tid in narratives.get(sid, []):
                if tid not in theme_cluster_map:
                    theme_cluster_map[tid] = set()
                theme_cluster_map[tid].add(ci)

    for i in range(len(theme_ids_list)):
        for j in range(i + 1, len(theme_ids_list)):
            ta = theme_ids_list[i]
            tb = theme_ids_list[j]
            # Do they appear in different clusters?
            ca = theme_cluster_map.get(ta, set())
            cb = theme_cluster_map.get(tb, set())
            if ca and cb and ca != cb:
                # Do they ever appear together in the same study?
                co_occur = False
                for sid in study_ids:
                    st = study_theme_set.get(sid, set())
                    if ta in st and tb in st:
                        co_occur = True
                        break
                n_theme_pairs += 1
                if not co_occur:
                    n_incommensurable += 1

    incommensurability = (
        n_incommensurable / n_theme_pairs if n_theme_pairs > 0 else 0.0
    )

    # ---- Bridging themes ----
    # Themes that appear in >= 2 clusters
    bridging_themes = [
        tid for tid, cset in theme_cluster_map.items()
        if len(cset) >= 2
    ]

    return {
        "narratives": narratives,
        "clusters": clusters,
        "narrative_similarity_matrix": similarity_matrix,
        "n_traditions": n_traditions,
        "paradigm_evolution": paradigm_evolution,
        "incommensurability_index": incommensurability,
        "bridging_themes": bridging_themes,
    }
