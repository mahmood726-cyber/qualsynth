"""Causal loop diagram extraction from qualitative findings.

Pure Python implementation (no numpy/scipy). Scans study text for
causal language, maps cause/effect phrases to themes, builds a
directed causal graph, and detects feedback loops and leverage points.
"""

import re


# ---- Causal connectors with polarity ----

# (pattern, direction): direction is "+" for enabling/increasing, "-" for inhibiting
CAUSAL_PATTERNS = [
    # Positive direction connectors
    (re.compile(r"\bleads?\s+to\b", re.IGNORECASE), "+"),
    (re.compile(r"\bcauses?\b", re.IGNORECASE), "+"),
    (re.compile(r"\bcausing\b", re.IGNORECASE), "+"),
    (re.compile(r"\bresults?\s+in\b", re.IGNORECASE), "+"),
    (re.compile(r"\bcontributes?\s+to\b", re.IGNORECASE), "+"),
    (re.compile(r"\binfluences?\b", re.IGNORECASE), "+"),
    (re.compile(r"\baffects?\b", re.IGNORECASE), "+"),
    (re.compile(r"\bdetermines?\b", re.IGNORECASE), "+"),
    (re.compile(r"\btriggers?\b", re.IGNORECASE), "+"),
    (re.compile(r"\benables?\b", re.IGNORECASE), "+"),
    (re.compile(r"\bfacilitates?\b", re.IGNORECASE), "+"),
    (re.compile(r"\bincreases?\b", re.IGNORECASE), "+"),
    (re.compile(r"\bstrengthens?\b", re.IGNORECASE), "+"),
    (re.compile(r"\bpromotes?\b", re.IGNORECASE), "+"),
    (re.compile(r"\bencourages?\b", re.IGNORECASE), "+"),
    (re.compile(r"\bbecause\b", re.IGNORECASE), "+"),
    # Negative direction connectors
    (re.compile(r"\bprevents?\b", re.IGNORECASE), "-"),
    (re.compile(r"\breduces?\b", re.IGNORECASE), "-"),
    (re.compile(r"\bhinders?\b", re.IGNORECASE), "-"),
    (re.compile(r"\bimpedes?\b", re.IGNORECASE), "-"),
    (re.compile(r"\bblocks?\b", re.IGNORECASE), "-"),
    (re.compile(r"\binhibits?\b", re.IGNORECASE), "-"),
    (re.compile(r"\bdiminishes?\b", re.IGNORECASE), "-"),
    (re.compile(r"\bundermines?\b", re.IGNORECASE), "-"),
    (re.compile(r"\bdecreases?\b", re.IGNORECASE), "-"),
    (re.compile(r"\blimits?\b", re.IGNORECASE), "-"),
]

_SPLIT_RE = re.compile(r"[^a-zA-Z]+")


def _tokenize(text):
    """Lowercase and split on non-alpha."""
    return [t for t in _SPLIT_RE.split(text.lower()) if t]


def _split_sentences(text):
    """Split text into sentences on punctuation boundaries."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def _study_text_parts(study):
    """Collect all text parts for a study."""
    parts = list(study.key_findings)
    for q in study.quotes:
        parts.append(q.text)
    return parts


def _extract_causal_claims(text):
    """Extract causal claims from a single sentence.

    Returns list of (cause_phrase, effect_phrase, direction).
    The cause_phrase is the text before the connector; effect_phrase after.
    """
    claims = []
    for pattern, direction in CAUSAL_PATTERNS:
        match = pattern.search(text)
        if match:
            before = text[:match.start()].strip()
            after = text[match.end():].strip()
            # Clean up: take last meaningful chunk before and first after
            cause = before if before else "unknown"
            effect = after if after else "unknown"
            # Trim to reasonable length
            cause = cause[-120:].strip()
            effect = effect[:120].strip()
            if cause and effect and cause != "unknown" and effect != "unknown":
                claims.append((cause, effect, direction))
    return claims


def _match_to_theme(phrase, themes):
    """Match a cause/effect phrase to the best-matching theme.

    Uses keyword overlap between phrase tokens and theme label + concepts.
    Returns theme_id or None.
    """
    phrase_tokens = set(_tokenize(phrase))
    if not phrase_tokens:
        return None

    best_theme = None
    best_score = 0

    for t in themes:
        theme_tokens = set(_tokenize(t.label))
        for concept in t.concepts:
            theme_tokens.update(_tokenize(concept))

        overlap = len(phrase_tokens & theme_tokens)
        if overlap > best_score:
            best_score = overlap
            best_theme = t.theme_id

    return best_theme if best_score > 0 else None


# ---- Cycle detection via DFS ----

def _find_cycles(adj, nodes):
    """Find all simple cycles in a directed graph using DFS.

    adj: dict {node: set of successors}
    nodes: list of all node ids

    Returns list of cycles, each cycle is a list of node ids.
    """
    cycles = []
    node_set = set(nodes)

    def _dfs(start, current, path, visited):
        for neighbor in adj.get(current, set()):
            if neighbor == start and len(path) >= 2:
                cycles.append(list(path))
            elif neighbor not in visited and neighbor in node_set:
                visited.add(neighbor)
                path.append(neighbor)
                _dfs(start, neighbor, path, visited)
                path.pop()
                visited.discard(neighbor)

    for node in nodes:
        _dfs(node, node, [node], {node})

    # Deduplicate cycles: normalize by rotating to start with min element
    seen = set()
    unique_cycles = []
    for cycle in cycles:
        # Rotate so smallest element is first
        min_idx = cycle.index(min(cycle))
        rotated = tuple(cycle[min_idx:] + cycle[:min_idx])
        if rotated not in seen:
            seen.add(rotated)
            unique_cycles.append(list(rotated))

    return unique_cycles


# ---- Public API ----

def analyse_causal_map(studies, themes):
    """Extract causal relationships and build a causal loop diagram.

    Args:
        studies: list of StudyInput
        themes: list of Theme (with concepts and assigned_studies populated)

    Returns:
        dict with keys:
            causal_edges: list of {cause_theme, effect_theme, direction, count}
            feedback_loops: list of {themes, type}
            leverage_themes: list of {theme_id, score}
            causal_density: float
            n_causal_claims: int
            system_archetypes: list of str
            causal_matrix: dict {(theme_a, theme_b): direction}
    """
    theme_ids = [t.theme_id for t in themes]
    theme_map = {t.theme_id: t for t in themes}

    # ---- Extract all causal claims ----
    all_claims = []  # (cause_phrase, effect_phrase, direction)
    total_sentences = 0

    for s in studies:
        parts = _study_text_parts(s)
        for part in parts:
            sentences = _split_sentences(part)
            total_sentences += len(sentences)
            for sent in sentences:
                claims = _extract_causal_claims(sent)
                all_claims.extend(claims)

    n_causal_claims = len(all_claims)

    # ---- Map claims to themes ----
    edge_counts = {}  # (cause_theme, effect_theme) -> {direction, count}
    for cause_phrase, effect_phrase, direction in all_claims:
        cause_theme = _match_to_theme(cause_phrase, themes)
        effect_theme = _match_to_theme(effect_phrase, themes)
        if cause_theme and effect_theme and cause_theme != effect_theme:
            key = (cause_theme, effect_theme)
            if key not in edge_counts:
                edge_counts[key] = {"direction": direction, "count": 0}
            edge_counts[key]["count"] += 1
            # Direction: majority vote (keep most recent for simplicity)
            edge_counts[key]["direction"] = direction

    # ---- Build causal edges list ----
    causal_edges = []
    for (ct, et), info in edge_counts.items():
        causal_edges.append({
            "cause_theme": ct,
            "effect_theme": et,
            "direction": info["direction"],
            "count": info["count"],
        })

    # ---- Build causal matrix ----
    causal_matrix = {}
    for (ct, et), info in edge_counts.items():
        causal_matrix[(ct, et)] = info["direction"]

    # ---- Build adjacency for cycle detection ----
    adj = {tid: set() for tid in theme_ids}
    for (ct, et) in edge_counts:
        if ct in adj:
            adj[ct].add(et)

    # ---- Feedback loop detection ----
    active_nodes = [tid for tid in theme_ids if adj.get(tid)]
    # Include nodes that are targets too
    target_nodes = set()
    for (ct, et) in edge_counts:
        target_nodes.add(ct)
        target_nodes.add(et)
    active_nodes = [tid for tid in theme_ids if tid in target_nodes]

    raw_cycles = _find_cycles(adj, active_nodes)

    feedback_loops = []
    for cycle in raw_cycles:
        # Count negative edges in cycle
        n_negative = 0
        for i in range(len(cycle)):
            a = cycle[i]
            b = cycle[(i + 1) % len(cycle)]
            edge_dir = causal_matrix.get((a, b), "+")
            if edge_dir == "-":
                n_negative += 1
        # Even number of negatives = reinforcing; odd = balancing
        loop_type = "reinforcing" if n_negative % 2 == 0 else "balancing"
        feedback_loops.append({
            "themes": cycle,
            "type": loop_type,
        })

    # ---- Leverage points ----
    out_degree = {tid: 0 for tid in theme_ids}
    in_degree = {tid: 0 for tid in theme_ids}
    for (ct, et) in edge_counts:
        out_degree[ct] = out_degree.get(ct, 0) + 1
        in_degree[et] = in_degree.get(et, 0) + 1

    leverage_themes = []
    for tid in theme_ids:
        score = out_degree.get(tid, 0) / max(1, in_degree.get(tid, 0))
        if out_degree.get(tid, 0) > 0 or in_degree.get(tid, 0) > 0:
            leverage_themes.append({"theme_id": tid, "score": score})

    leverage_themes.sort(key=lambda x: x["score"], reverse=True)

    # ---- Causal density ----
    causal_density = n_causal_claims / total_sentences if total_sentences > 0 else 0.0

    # ---- System archetype detection ----
    system_archetypes = []
    # Check for reinforcing loops with >= 3 nodes
    for loop in feedback_loops:
        if loop["type"] == "reinforcing" and len(loop["themes"]) >= 3:
            if "Reinforcing loop (>=3 nodes)" not in system_archetypes:
                system_archetypes.append("Reinforcing loop (>=3 nodes)")
            break

    # Check for "Fixes that fail" pattern: any reinforcing cycle of length 3
    for loop in feedback_loops:
        if loop["type"] == "reinforcing" and len(loop["themes"]) == 3:
            if "Fixes that fail" not in system_archetypes:
                system_archetypes.append("Fixes that fail")
            break

    # Check for "Shifting the burden": two parallel paths between any pair
    for t1 in theme_ids:
        for t2 in theme_ids:
            if t1 == t2:
                continue
            # Direct edge t1->t2
            if (t1, t2) in edge_counts:
                # Check for indirect path t1->x->t2
                for mid in theme_ids:
                    if mid == t1 or mid == t2:
                        continue
                    if (t1, mid) in edge_counts and (mid, t2) in edge_counts:
                        if "Shifting the burden" not in system_archetypes:
                            system_archetypes.append("Shifting the burden")
                        break
            if "Shifting the burden" in system_archetypes:
                break
        if "Shifting the burden" in system_archetypes:
            break

    return {
        "causal_edges": causal_edges,
        "feedback_loops": feedback_loops,
        "leverage_themes": leverage_themes,
        "causal_density": causal_density,
        "n_causal_claims": n_causal_claims,
        "system_archetypes": system_archetypes,
        "causal_matrix": causal_matrix,
    }
