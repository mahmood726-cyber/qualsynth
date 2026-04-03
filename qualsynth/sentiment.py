"""Lexicon-based sentiment analysis for qualitative findings.

Pure Python implementation (no numpy/scipy). Scores study-level and
theme-level sentiment from key_findings and quotes, detects basic
emotions, and computes sentiment trajectory over time.
"""

import re

# ---- Built-in sentiment lexicon (~200 words) ----

POSITIVE_WORDS = frozenset([
    "benefit", "effective", "improve", "success", "strength", "enable",
    "support", "hope", "comfort", "empowerment", "resilience", "satisfaction",
    "confidence", "progress", "wellbeing", "encourage", "enjoy", "happy",
    "heal", "helpful", "inspire", "joy", "kind", "love", "motivate",
    "optimism", "peace", "pleasure", "positive", "protect", "recover",
    "relief", "resolve", "reward", "safe", "secure", "skill", "thrive",
    "trust", "valuable", "welcome", "worthy", "accomplish", "achieve",
    "admire", "appreciate", "calm", "capable", "celebrate", "cherish",
    "collaborate", "compassion", "cooperate", "courage", "creative",
    "delight", "dignity", "eager", "empower", "energize", "enrich",
    "enthusiastic", "excellence", "faith", "flourish", "fortunate",
    "freedom", "generous", "gentle", "glad", "graceful", "grateful",
    "growth", "harmony", "healthy", "heartfelt", "honour", "hopeful",
    "ideal", "inclusive", "independence", "innovative", "integrity",
    "joyful", "liberate", "meaningful", "nurture", "overcome", "patience",
    "pleased", "praise", "productive", "profound", "prosper", "proud",
    "purpose", "reassure", "respect", "restore", "robust", "serene",
    "sincere", "stable", "strengthen", "sympathetic", "thankful",
    "transform", "triumph", "understanding", "uplift", "vibrant", "vital",
])

NEGATIVE_WORDS = frozenset([
    "barrier", "challenge", "difficult", "struggle", "burden", "frustration",
    "anxiety", "fear", "pain", "isolation", "stigma", "failure", "loss",
    "distress", "overwhelm", "abandon", "abuse", "ache", "afraid", "agony",
    "anger", "anguish", "annoy", "ashamed", "avoid", "blame", "boring",
    "broke", "chaos", "conflict", "confuse", "cruel", "danger", "death",
    "decline", "defeat", "deny", "depressed", "despair", "destroy",
    "disappoint", "discomfort", "discourage", "disease", "disgust",
    "dismiss", "disrupt", "doubt", "dread", "empty", "enemy", "exhaust",
    "fatigue", "fault", "frightened", "grief", "guilt", "harm", "hate",
    "helpless", "hopeless", "hostile", "hurt", "ignore", "impair",
    "inadequate", "inferior", "injure", "insecure", "irritate", "jealous",
    "lack", "limit", "lonely", "miserable", "mistake", "neglect", "nervous",
    "obstacle", "offend", "oppress", "painful", "panic", "pessimistic",
    "poor", "pressure", "problem", "punish", "rage", "regret", "reject",
    "resent", "risk", "ruin", "sad", "scare", "severe", "shame", "shock",
    "sick", "stress", "suffer", "terrible", "threat", "tired", "tragic",
    "trauma", "trouble", "ugly", "uncertain", "unhappy", "victim", "weak",
    "worry", "worse", "worthless",
])

INTENSIFIERS = frozenset([
    "very", "extremely", "highly", "significantly", "incredibly",
    "exceptionally", "remarkably", "tremendously",
])

NEGATORS = frozenset([
    "not", "no", "never", "neither", "hardly", "barely", "scarcely",
])

# ---- Emotion keyword mappings ----

EMOTION_KEYWORDS = {
    "joy": frozenset([
        "happy", "pleased", "grateful", "joyful", "delighted", "glad",
        "cheerful", "content", "elated", "ecstatic",
    ]),
    "sadness": frozenset([
        "sad", "grief", "loss", "mourn", "sorrow", "melancholy",
        "heartbroken", "tearful", "bereaved", "dejected",
    ]),
    "fear": frozenset([
        "afraid", "worried", "anxious", "scared", "frightened", "dread",
        "terrified", "panic", "nervous", "apprehensive",
    ]),
    "anger": frozenset([
        "angry", "frustrated", "resentful", "furious", "rage", "hostile",
        "irritated", "outraged", "bitter", "annoyed",
    ]),
    "surprise": frozenset([
        "unexpected", "shocked", "astonished", "amazed", "startled",
        "stunned", "bewildered", "overwhelmed", "incredulous", "sudden",
    ]),
    "trust": frozenset([
        "reliable", "confident", "safe", "trustworthy", "dependable",
        "faithful", "loyal", "secure", "credible", "assured",
    ]),
}


# ---- Internal helpers ----

_SPLIT_RE = re.compile(r"[^a-zA-Z]+")


def _tokenize_sentence(text):
    """Lowercase and split on non-alpha characters."""
    return [t for t in _SPLIT_RE.split(text.lower()) if t]


def _split_sentences(text):
    """Naively split on sentence-ending punctuation."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def _score_sentence(tokens):
    """Score a single tokenised sentence.

    Returns (positive_count, negative_count, total_scored_words).
    Handles intensifiers (x1.5) and negators (flip within 3-word window).
    """
    pos_count = 0.0
    neg_count = 0.0
    total_scored = 0

    # Track negation window
    negation_active = 0  # countdown of words in negation window

    for tok in tokens:
        if tok in NEGATORS:
            negation_active = 3
            continue

        is_intensifier = tok in INTENSIFIERS
        if is_intensifier:
            # Intensifiers don't count as scored words themselves
            continue

        multiplier = 1.0
        # Look back: check if previous token was intensifier
        # (simplified: use a lookahead approach below instead)

        is_pos = tok in POSITIVE_WORDS
        is_neg = tok in NEGATIVE_WORDS

        if is_pos or is_neg:
            total_scored += 1

            if is_pos:
                if negation_active > 0:
                    neg_count += 1.0
                else:
                    pos_count += 1.0
            elif is_neg:
                if negation_active > 0:
                    pos_count += 1.0
                else:
                    neg_count += 1.0

        if negation_active > 0:
            negation_active -= 1

    # Second pass: apply intensifier boost
    # Re-scan for intensifier + sentiment word pairs
    for i, tok in enumerate(tokens):
        if tok in INTENSIFIERS and i + 1 < len(tokens):
            next_tok = tokens[i + 1]
            if next_tok in POSITIVE_WORDS or next_tok in NEGATIVE_WORDS:
                # Add the 0.5 extra (already counted 1.0 above)
                if next_tok in POSITIVE_WORDS:
                    # Check if negated
                    neg_window = any(
                        tokens[j] in NEGATORS
                        for j in range(max(0, i - 3), i)
                    )
                    if neg_window:
                        neg_count += 0.5
                    else:
                        pos_count += 0.5
                else:
                    neg_window = any(
                        tokens[j] in NEGATORS
                        for j in range(max(0, i - 3), i)
                    )
                    if neg_window:
                        pos_count += 0.5
                    else:
                        neg_count += 0.5

    return pos_count, neg_count, total_scored


def _sentence_sentiment(text):
    """Compute sentiment for a single sentence string.

    Returns a float in [-1, 1], or 0.0 if no scored words.
    """
    tokens = _tokenize_sentence(text)
    pos, neg, total = _score_sentence(tokens)
    if total == 0:
        return 0.0
    return (pos - neg) / total


def _study_text_parts(study):
    """Collect all text parts (key_findings + quote texts) for a study."""
    parts = list(study.key_findings)
    for q in study.quotes:
        parts.append(q.text)
    return parts


# ---- Rank correlation (Spearman) ----

def _rank(values):
    """Assign ranks to values (average rank for ties)."""
    n = len(values)
    indexed = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and values[indexed[j]] == values[indexed[i]]:
            j += 1
        avg_rank = (i + j - 1) / 2.0 + 1  # 1-based
        for k_idx in range(i, j):
            ranks[indexed[k_idx]] = avg_rank
        i = j
    return ranks


def _spearman_correlation(xs, ys):
    """Spearman rank correlation between two sequences.

    Returns float in [-1, 1], or 0.0 if degenerate.
    """
    n = len(xs)
    if n < 2:
        return 0.0
    rx = _rank(xs)
    ry = _rank(ys)
    mean_x = sum(rx) / n
    mean_y = sum(ry) / n
    num = sum((rx[i] - mean_x) * (ry[i] - mean_y) for i in range(n))
    den_x = sum((rx[i] - mean_x) ** 2 for i in range(n))
    den_y = sum((ry[i] - mean_y) ** 2 for i in range(n))
    den = (den_x * den_y) ** 0.5
    if den == 0.0:
        return 0.0
    return num / den


# ---- Public API ----

def analyse_sentiment(studies, themes):
    """Run full sentiment analysis on studies and themes.

    Args:
        studies: list of StudyInput
        themes: list of Theme (with assigned_studies populated)

    Returns:
        dict with keys:
            study_sentiments: dict {study_id: float} in [-1, 1]
            theme_sentiments: dict {theme_id: float} in [-1, 1]
            overall_sentiment: float in [-1, 1]
            sentiment_trajectory: list of {year, sentiment}
            emotion_profile: dict {emotion: int}
            sentiment_theme_correlation: float in [-1, 1]
    """
    # ---- Study-level sentiment ----
    study_sentiments = {}
    study_sentences_all = {}  # study_id -> list of sentence texts

    for s in studies:
        parts = _study_text_parts(s)
        sentences = []
        for part in parts:
            sentences.extend(_split_sentences(part))
        study_sentences_all[s.study_id] = sentences

        if not sentences:
            study_sentiments[s.study_id] = 0.0
            continue
        scores = [_sentence_sentiment(sent) for sent in sentences]
        study_sentiments[s.study_id] = sum(scores) / len(scores)

    # ---- Theme-level sentiment ----
    theme_sentiments = {}
    for t in themes:
        assigned = [sid for sid in t.assigned_studies if sid in study_sentiments]
        if not assigned:
            theme_sentiments[t.theme_id] = 0.0
        else:
            theme_sentiments[t.theme_id] = (
                sum(study_sentiments[sid] for sid in assigned) / len(assigned)
            )

    # ---- Overall sentiment ----
    if study_sentiments:
        overall = sum(study_sentiments.values()) / len(study_sentiments)
    else:
        overall = 0.0

    # ---- Sentiment trajectory (by year) ----
    year_map = {}  # year -> list of sentiments
    for s in studies:
        yr = s.year
        if yr not in year_map:
            year_map[yr] = []
        year_map[yr].append(study_sentiments.get(s.study_id, 0.0))

    trajectory = []
    for yr in sorted(year_map.keys()):
        vals = year_map[yr]
        trajectory.append({
            "year": yr,
            "sentiment": sum(vals) / len(vals),
        })

    # ---- Emotion detection ----
    emotion_profile = {emo: 0 for emo in EMOTION_KEYWORDS}
    for s in studies:
        sentences = study_sentences_all.get(s.study_id, [])
        for sent in sentences:
            tokens = set(_tokenize_sentence(sent))
            for emo, keywords in EMOTION_KEYWORDS.items():
                if tokens & keywords:
                    emotion_profile[emo] += 1

    # ---- Sentiment-theme correlation ----
    # Rank correlation between theme sentiment and theme saturation
    # (number of assigned studies / total studies)
    n_studies = len(studies)
    if len(themes) >= 2 and n_studies > 0:
        t_sents = []
        t_sats = []
        for t in themes:
            t_sents.append(theme_sentiments.get(t.theme_id, 0.0))
            t_sats.append(len(t.assigned_studies) / n_studies)
        correlation = _spearman_correlation(t_sents, t_sats)
    else:
        correlation = 0.0

    return {
        "study_sentiments": study_sentiments,
        "theme_sentiments": theme_sentiments,
        "overall_sentiment": overall,
        "sentiment_trajectory": trajectory,
        "emotion_profile": emotion_profile,
        "sentiment_theme_correlation": correlation,
    }
