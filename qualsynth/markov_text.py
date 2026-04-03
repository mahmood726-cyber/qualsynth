"""Markov Chain Narrative Generation for qualitative evidence synthesis.

Pure Python implementation (no numpy/scipy). Learns bigram and trigram
text models from study findings and quotes, generates synthesis narratives,
and computes perplexity and coherence metrics.
"""

import math
import random as _random_mod

from qualsynth.similarity import _tokenize


def _study_texts(study):
    """Collect all text from a study's key_findings and quotes."""
    parts = list(study.key_findings)
    for q in study.quotes:
        parts.append(q.text)
    return parts


def _all_sentences(studies):
    """Collect all sentences from all studies."""
    sentences = []
    for s in studies:
        sentences.extend(_study_texts(s))
    return sentences


def _tokenize_sentence(text):
    """Tokenize preserving sentence boundaries.

    Returns list of tokens including punctuation markers.
    Reuses _tokenize from similarity.py but also preserves sentence-end markers.
    """
    # Get clean tokens
    tokens = _tokenize(text)
    # Check if original text ends with sentence boundary
    stripped = text.strip()
    if stripped and stripped[-1] in '.!?':
        tokens.append('<END>')
    return tokens


def _build_bigram_model(sentences):
    """Build bigram transition model.

    Returns:
        bigram: dict {word: {next_word: probability}}
        unigram: dict {word: probability}
    """
    counts = {}  # {word: {next_word: count}}
    unigram_counts = {}

    for sent in sentences:
        tokens = _tokenize_sentence(sent)
        if len(tokens) < 2:
            continue
        for i in range(len(tokens) - 1):
            w1, w2 = tokens[i], tokens[i + 1]
            if w1 not in counts:
                counts[w1] = {}
            counts[w1][w2] = counts[w1].get(w2, 0) + 1
            unigram_counts[w1] = unigram_counts.get(w1, 0) + 1
        # Count last token too
        last = tokens[-1]
        unigram_counts[last] = unigram_counts.get(last, 0) + 1

    # Normalize to probabilities
    bigram = {}
    for w1, nexts in counts.items():
        total = sum(nexts.values())
        bigram[w1] = {w2: c / total for w2, c in nexts.items()}

    total_uni = sum(unigram_counts.values())
    unigram = {w: c / total_uni for w, c in unigram_counts.items()} if total_uni > 0 else {}

    return bigram, unigram


def _build_trigram_model(sentences):
    """Build trigram transition model.

    Returns:
        trigram: dict {(word_i, word_j): {word_k: probability}}
    """
    counts = {}  # {(w1, w2): {w3: count}}

    for sent in sentences:
        tokens = _tokenize_sentence(sent)
        if len(tokens) < 3:
            continue
        for i in range(len(tokens) - 2):
            key = (tokens[i], tokens[i + 1])
            w3 = tokens[i + 2]
            if key not in counts:
                counts[key] = {}
            counts[key][w3] = counts[key].get(w3, 0) + 1

    # Normalize
    trigram = {}
    for key, nexts in counts.items():
        total = sum(nexts.values())
        trigram[key] = {w3: c / total for w3, c in nexts.items()}

    return trigram


def _weighted_choice(prob_dict, rng):
    """Choose a key from {key: probability} dict using weighted random selection."""
    if not prob_dict:
        return None
    items = list(prob_dict.items())
    r = rng.random()
    cumulative = 0.0
    for word, prob in items:
        cumulative += prob
        if r <= cumulative:
            return word
    return items[-1][0]  # fallback for floating point edge case


def _generate_text(bigram, trigram, unigram, seed_words, max_words=50, rng=None):
    """Generate text using trigram model with bigram and unigram backoff.

    Args:
        bigram: bigram model dict
        trigram: trigram model dict
        unigram: unigram model dict
        seed_words: list of 1-2 seed words
        max_words: maximum number of words to generate
        rng: random.Random instance for reproducibility

    Returns:
        generated text string
    """
    if rng is None:
        rng = _random_mod.Random(42)

    tokens = list(seed_words)
    if not tokens:
        # Pick a random start from unigram
        if unigram:
            tokens = [_weighted_choice(unigram, rng)]
        else:
            return ""

    for _ in range(max_words - len(tokens)):
        next_word = None

        # Try trigram
        if len(tokens) >= 2:
            key = (tokens[-2], tokens[-1])
            if key in trigram:
                next_word = _weighted_choice(trigram[key], rng)

        # Backoff to bigram
        if next_word is None and tokens[-1] in bigram:
            next_word = _weighted_choice(bigram[tokens[-1]], rng)

        # Backoff to unigram
        if next_word is None and unigram:
            next_word = _weighted_choice(unigram, rng)

        if next_word is None:
            break

        if next_word == '<END>':
            break

        tokens.append(next_word)

    return " ".join(tokens)


def _compute_perplexity(bigram, unigram, sentences):
    """Compute perplexity of the bigram model on given sentences.

    PP = exp(-1/N * sum(log P(w_i | w_{i-1})))
    Lower = better model.
    """
    total_log_prob = 0.0
    n_tokens = 0
    vocab_size = len(unigram) if unigram else 1

    for sent in sentences:
        tokens = _tokenize_sentence(sent)
        if len(tokens) < 2:
            continue
        for i in range(1, len(tokens)):
            w_prev = tokens[i - 1]
            w_curr = tokens[i]
            if w_prev in bigram and w_curr in bigram[w_prev]:
                prob = bigram[w_prev][w_curr]
            elif w_curr in unigram:
                # Backoff to unigram with smoothing
                prob = unigram[w_curr] * 0.1  # discount factor
            else:
                # Laplace smoothing fallback
                prob = 1.0 / (vocab_size + 1)

            if prob > 0:
                total_log_prob += math.log(prob)
            n_tokens += 1

    if n_tokens == 0:
        return float('inf')

    return math.exp(-total_log_prob / n_tokens)


def _compute_coherence(generated_text, bigram):
    """Compute coherence: proportion of generated bigrams that appear in training data."""
    tokens = _tokenize(generated_text)
    if len(tokens) < 2:
        return 0.0

    n_bigrams = 0
    n_found = 0
    for i in range(len(tokens) - 1):
        w1, w2 = tokens[i], tokens[i + 1]
        n_bigrams += 1
        if w1 in bigram and w2 in bigram[w1]:
            n_found += 1

    return n_found / n_bigrams if n_bigrams > 0 else 0.0


def _theme_conditioned_texts(studies, themes, bigram_all, trigram_all, unigram_all, rng):
    """Generate text conditioned on each theme.

    For each theme, filter studies to those assigned to the theme,
    build a theme-specific model, and generate text.
    """
    theme_texts = {}
    for theme in themes:
        assigned = set(theme.assigned_studies)
        if not assigned:
            theme_texts[theme.theme_id] = ""
            continue

        # Filter studies
        theme_studies = [s for s in studies if s.study_id in assigned]
        if not theme_studies:
            theme_texts[theme.theme_id] = ""
            continue

        # Build theme-specific sentences
        sentences = _all_sentences(theme_studies)
        if not sentences:
            theme_texts[theme.theme_id] = ""
            continue

        # Build theme-specific models
        t_bigram, t_unigram = _build_bigram_model(sentences)
        t_trigram = _build_trigram_model(sentences)

        # Pick seed from theme-specific unigram
        if t_unigram:
            seed = [_weighted_choice(t_unigram, rng)]
        else:
            seed = []

        text = _generate_text(t_bigram, t_trigram, t_unigram, seed, max_words=30, rng=rng)
        theme_texts[theme.theme_id] = text

    return theme_texts


# ---------- Public API ----------

def generate_markov_narrative(studies, themes=None, seed=42, max_words=50):
    """Learn text patterns and generate synthesis narratives.

    Args:
        studies: list of StudyInput
        themes: optional list of Theme (for theme-conditioned generation)
        seed: random seed for reproducibility
        max_words: max words in generated text

    Returns:
        dict with keys:
            bigram_vocab_size: int
            trigram_vocab_size: int
            generated_text: str (~50 words)
            perplexity: float
            coherence_score: float
            theme_texts: dict {theme_id: generated str}
    """
    rng = _random_mod.Random(seed)

    if not studies:
        return {
            "bigram_vocab_size": 0,
            "trigram_vocab_size": 0,
            "generated_text": "",
            "perplexity": float('inf'),
            "coherence_score": 0.0,
            "theme_texts": {},
        }

    # Collect all sentences
    sentences = _all_sentences(studies)
    if not sentences:
        return {
            "bigram_vocab_size": 0,
            "trigram_vocab_size": 0,
            "generated_text": "",
            "perplexity": float('inf'),
            "coherence_score": 0.0,
            "theme_texts": {},
        }

    # Build models
    bigram, unigram = _build_bigram_model(sentences)
    trigram = _build_trigram_model(sentences)

    # Pick seed words from most common unigrams
    if unigram:
        top_words = sorted(unigram.items(), key=lambda x: x[1], reverse=True)
        # Pick two seed words
        seed_words = [top_words[0][0]]
        if len(top_words) > 1:
            # Find a word that follows the first seed
            if seed_words[0] in bigram:
                second = _weighted_choice(bigram[seed_words[0]], rng)
                if second and second != '<END>':
                    seed_words.append(second)
    else:
        seed_words = []

    # Generate text
    generated = _generate_text(bigram, trigram, unigram, seed_words, max_words=max_words, rng=rng)

    # Compute perplexity on training data (as a quality measure)
    perplexity = _compute_perplexity(bigram, unigram, sentences)

    # Compute coherence of generated text
    coherence = _compute_coherence(generated, bigram)

    # Theme-conditioned generation
    theme_texts = {}
    if themes:
        theme_texts = _theme_conditioned_texts(studies, themes, bigram, trigram, unigram, rng)

    return {
        "bigram_vocab_size": len(bigram),
        "trigram_vocab_size": len(trigram),
        "generated_text": generated,
        "perplexity": perplexity,
        "coherence_score": coherence,
        "theme_texts": theme_texts,
    }
