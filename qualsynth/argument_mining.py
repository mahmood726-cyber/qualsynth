"""Argument Structure Extraction from qualitative findings.

Detects claim-evidence-reasoning structures in study findings
and quotes, maps support/refute relationships between themes,
and computes argument strength metrics.

Pure Python implementation (no numpy/scipy).
"""


# ---------- Indicator word lists ----------

CLAIM_INDICATORS = frozenset([
    "suggest", "suggests", "suggesting", "suggested",
    "indicate", "indicates", "indicating", "indicated",
    "demonstrate", "demonstrates", "demonstrating", "demonstrated",
    "show", "shows", "showed", "shown",
    "found", "finding",
    "reported", "reporting",
    "revealed", "revealing",
    "concluded", "concluding",
])

# Phrases that need multi-word matching
CLAIM_PHRASES = [
    "show that", "found that",
]

EVIDENCE_INDICATORS = frozenset([
    "participant", "participants",
    "interviewee", "interviewees",
    "respondent", "respondents",
    "stated", "described", "explained",
])

EVIDENCE_PHRASES = [
    "one participant", "several", "many", "most",
]

REASONING_INDICATORS = frozenset([
    "because", "therefore", "thus", "consequently",
])

REASONING_PHRASES = [
    "as a result", "this means", "this suggests", "implying",
]

NEGATION_WORDS = frozenset([
    "not", "no", "contrary", "despite", "however",
    "never", "neither", "nor", "without",
])


# ---------- Sentence splitting ----------

def _split_sentences(text):
    """Split text into sentences on '. ', '? ', '! ' boundaries."""
    sentences = []
    current = []
    i = 0
    while i < len(text):
        current.append(text[i])
        if text[i] in ".?!" and i + 1 < len(text) and text[i + 1] == " ":
            sentence = "".join(current).strip()
            if sentence:
                sentences.append(sentence)
            current = []
            i += 2  # skip the space
            continue
        i += 1
    # Remaining text
    leftover = "".join(current).strip()
    if leftover:
        sentences.append(leftover)
    return sentences


# ---------- Indicator counting ----------

def _count_indicators(sentence, word_set, phrase_list):
    """Count how many indicator words/phrases appear in a sentence."""
    lower = sentence.lower()
    count = 0
    # Word-level matching
    words = lower.split()
    for w in words:
        # Strip punctuation for matching
        cleaned = w.strip(".,;:!?\"'()-")
        if cleaned in word_set:
            count += 1
    # Phrase-level matching
    for phrase in phrase_list:
        if phrase in lower:
            count += 1
    return count


def _classify_sentence(sentence):
    """Classify a sentence as claim, evidence, or reasoning.

    Returns (type_str, claim_count, evidence_count, reasoning_count).
    """
    c_count = _count_indicators(sentence, CLAIM_INDICATORS, CLAIM_PHRASES)
    e_count = _count_indicators(sentence, EVIDENCE_INDICATORS, EVIDENCE_PHRASES)
    r_count = _count_indicators(sentence, REASONING_INDICATORS, REASONING_PHRASES)

    max_count = max(c_count, e_count, r_count)
    if max_count == 0:
        # Default: classify as claim (descriptive statement)
        return "claim", c_count, e_count, r_count

    if c_count >= e_count and c_count >= r_count:
        return "claim", c_count, e_count, r_count
    elif e_count >= r_count:
        return "evidence", c_count, e_count, r_count
    else:
        return "reasoning", c_count, e_count, r_count


# ---------- Argument unit grouping ----------

def _extract_argument_units(studies):
    """Extract argument units from all study findings and quotes.

    Each unit is a group of consecutive sentences of the same type
    within a single study's finding or quote.

    Returns:
        list of dicts: {text, type, study_id, sentences}
    """
    units = []

    for study in studies:
        # Process key_findings
        for finding in study.key_findings:
            sentences = _split_sentences(finding)
            _group_sentences_into_units(sentences, study.study_id, units)

        # Process quotes
        for quote in study.quotes:
            sentences = _split_sentences(quote.text)
            _group_sentences_into_units(sentences, study.study_id, units)

    return units


def _group_sentences_into_units(sentences, study_id, units):
    """Group consecutive same-type sentences into argument units."""
    if not sentences:
        return

    current_type = None
    current_sentences = []

    for sent in sentences:
        sent_type, _, _, _ = _classify_sentence(sent)

        if sent_type == current_type:
            current_sentences.append(sent)
        else:
            if current_sentences:
                units.append({
                    "text": " ".join(current_sentences),
                    "type": current_type,
                    "study_id": study_id,
                    "sentences": list(current_sentences),
                })
            current_type = sent_type
            current_sentences = [sent]

    if current_sentences:
        units.append({
            "text": " ".join(current_sentences),
            "type": current_type,
            "study_id": study_id,
            "sentences": list(current_sentences),
        })


# ---------- Theme-argument mapping ----------

def _text_mentions_theme(text, theme):
    """Check if text references a theme (by label or concepts)."""
    lower = text.lower()
    # Check theme label words
    label_words = theme.label.lower().split()
    for word in label_words:
        word = word.strip(".,;:!?\"'()-")
        if len(word) > 2 and word in lower:
            return True
    # Check concepts
    for concept in theme.concepts:
        if concept.lower() in lower:
            return True
    return False


def _has_negation_near_theme(text, theme):
    """Check if negation words appear near theme references."""
    lower = text.lower()
    words = lower.split()
    label_words = set(
        w.strip(".,;:!?\"'()-") for w in theme.label.lower().split()
        if len(w.strip(".,;:!?\"'()-")) > 2
    )

    for i, w in enumerate(words):
        cleaned = w.strip(".,;:!?\"'()-")
        if cleaned in label_words:
            # Check window of 5 words before and after
            start = max(0, i - 5)
            end = min(len(words), i + 6)
            window = words[start:end]
            for ww in window:
                ww_clean = ww.strip(".,;:!?\"'()-")
                if ww_clean in NEGATION_WORDS:
                    return True
    return False


def _map_units_to_themes(units, themes):
    """Map argument units to themes and build theme argument maps.

    Returns:
        theme_arguments: dict theme_id -> {claims, evidence, reasoning}
    """
    theme_arguments = {}
    for theme in themes:
        theme_arguments[theme.theme_id] = {
            "claims": [],
            "evidence": [],
            "reasoning": [],
        }

    # Map singular type names to plural dict keys
    type_to_key = {"claim": "claims", "evidence": "evidence", "reasoning": "reasoning"}

    for unit in units:
        for theme in themes:
            # Check if the unit's study is assigned to this theme
            study_match = unit["study_id"] in theme.assigned_studies
            # Check if text mentions the theme
            text_match = _text_mentions_theme(unit["text"], theme)

            if study_match or text_match:
                key = type_to_key.get(unit["type"], "claims")
                theme_arguments[theme.theme_id][key].append(unit)

    return theme_arguments


# ---------- Support/refute relationships ----------

def _find_relationships(units, themes):
    """Find support/refute relationships between themes.

    - If a claim about theme A and evidence about theme B co-occur
      in the same study, mark as 'supports'.
    - If claim contains negation near theme reference, mark as 'refutes'.
    """
    relationships = []
    seen = set()

    # Group units by study
    study_units = {}
    for unit in units:
        sid = unit["study_id"]
        if sid not in study_units:
            study_units[sid] = []
        study_units[sid].append(unit)

    for sid, s_units in study_units.items():
        claims = [u for u in s_units if u["type"] == "claim"]
        evidence = [u for u in s_units if u["type"] == "evidence"]

        for claim_unit in claims:
            for theme_a in themes:
                if not _text_mentions_theme(claim_unit["text"], theme_a):
                    if theme_a.assigned_studies and sid not in theme_a.assigned_studies:
                        continue

                for ev_unit in evidence:
                    for theme_b in themes:
                        if theme_b.theme_id == theme_a.theme_id:
                            continue
                        if not _text_mentions_theme(ev_unit["text"], theme_b):
                            if theme_b.assigned_studies and sid not in theme_b.assigned_studies:
                                continue

                        key = (theme_a.theme_id, theme_b.theme_id)
                        rev_key = (theme_b.theme_id, theme_a.theme_id)

                        if key in seen or rev_key in seen:
                            continue

                        # Check for negation
                        if _has_negation_near_theme(claim_unit["text"], theme_b):
                            rel_type = "refutes"
                        else:
                            rel_type = "supports"

                        relationships.append({
                            "from": theme_a.theme_id,
                            "to": theme_b.theme_id,
                            "type": rel_type,
                        })
                        seen.add(key)

    return relationships


# ---------- Argument strength ----------

def _compute_argument_strength(theme_arguments):
    """Compute argument strength per theme.

    Strength = (n_evidence + n_reasoning) / max(1, n_claims).
    Higher means better supported claims.
    """
    strength = {}
    for theme_id, args in theme_arguments.items():
        n_claims = len(args["claims"])
        n_evidence = len(args["evidence"])
        n_reasoning = len(args["reasoning"])
        strength[theme_id] = (n_evidence + n_reasoning) / max(1, n_claims)
    return strength


# ---------- Public API ----------

def extract_arguments(studies, themes):
    """Extract argument structures from qualitative findings.

    Args:
        studies: list of StudyInput
        themes: list of Theme

    Returns:
        dict with keys:
            argument_units: list of {text, type, study_id}
            theme_arguments: dict theme_id -> {claims, evidence, reasoning}
            argument_strength: dict theme_id -> float
            support_relations: list of {from, to, type}
            total_claims: int
            total_evidence: int
            total_reasoning: int
    """
    units = _extract_argument_units(studies)

    theme_arguments = _map_units_to_themes(units, themes)
    strength = _compute_argument_strength(theme_arguments)
    relationships = _find_relationships(units, themes)

    # Count totals
    total_claims = sum(1 for u in units if u["type"] == "claim")
    total_evidence = sum(1 for u in units if u["type"] == "evidence")
    total_reasoning = sum(1 for u in units if u["type"] == "reasoning")

    # Clean up units for output (remove internal 'sentences' field)
    output_units = [
        {"text": u["text"], "type": u["type"], "study_id": u["study_id"]}
        for u in units
    ]

    # Clean up theme_arguments for output
    output_theme_args = {}
    for tid, args in theme_arguments.items():
        output_theme_args[tid] = {
            "claims": [{"text": u["text"], "type": u["type"], "study_id": u["study_id"]}
                       for u in args["claims"]],
            "evidence": [{"text": u["text"], "type": u["type"], "study_id": u["study_id"]}
                         for u in args["evidence"]],
            "reasoning": [{"text": u["text"], "type": u["type"], "study_id": u["study_id"]}
                          for u in args["reasoning"]],
        }

    return {
        "argument_units": output_units,
        "theme_arguments": output_theme_args,
        "argument_strength": strength,
        "support_relations": relationships,
        "total_claims": total_claims,
        "total_evidence": total_evidence,
        "total_reasoning": total_reasoning,
    }
