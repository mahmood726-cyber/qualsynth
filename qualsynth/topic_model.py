"""Simplified Latent Dirichlet Allocation via collapsed Gibbs sampling.

Pure Python implementation (no numpy/scipy). Discovers latent topics
from study texts (key_findings + quotes), computes per-study topic
proportions, perplexity, and PMI-based topic coherence.
"""

import math
import random

from qualsynth.similarity import _tokenize


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _study_text(study):
    """Concatenate key_findings and quote texts for a study."""
    parts = list(study.key_findings)
    for q in study.quotes:
        parts.append(q.text)
    return " ".join(parts)


def _build_corpus(studies):
    """Tokenize all studies and build word-to-id mapping.

    Returns:
        docs: list of list-of-int (word ids per study)
        vocab: list of str (index -> word)
        word2id: dict str -> int
    """
    vocab_set = set()
    raw_docs = []
    for s in studies:
        tokens = _tokenize(_study_text(s))
        raw_docs.append(tokens)
        vocab_set.update(tokens)
    vocab = sorted(vocab_set)
    word2id = {w: i for i, w in enumerate(vocab)}
    docs = [[word2id[t] for t in tokens] for tokens in raw_docs]
    return docs, vocab, word2id


# ---------------------------------------------------------------------------
# Collapsed Gibbs Sampler
# ---------------------------------------------------------------------------

def _gibbs_sample(docs, V, K, alpha, beta, n_iter, rng):
    """Run collapsed Gibbs sampling for LDA.

    Args:
        docs: list of list-of-int (word ids)
        V: vocabulary size
        K: number of topics
        alpha: Dirichlet prior on per-doc topic distributions
        beta: Dirichlet prior on per-topic word distributions
        n_iter: number of sampling iterations
        rng: random.Random instance

    Returns:
        z: list of list-of-int (topic assignments, same shape as docs)
        n_dk: list of list-of-int (D x K) count of words in doc d assigned to topic k
        n_kw: list of list-of-int (K x V) count of word w assigned to topic k
        n_k: list-of-int (K,) total words assigned to each topic
    """
    D = len(docs)

    # Initialise counts
    n_dk = [[0] * K for _ in range(D)]
    n_kw = [[0] * V for _ in range(K)]
    n_k = [0] * K

    # Random initialisation of topic assignments
    z = []
    for d in range(D):
        z_doc = []
        for n in range(len(docs[d])):
            k = rng.randint(0, K - 1)
            z_doc.append(k)
            w = docs[d][n]
            n_dk[d][k] += 1
            n_kw[k][w] += 1
            n_k[k] += 1
        z.append(z_doc)

    V_beta = V * beta

    # Gibbs iterations
    for _iteration in range(n_iter):
        for d in range(D):
            for n in range(len(docs[d])):
                w = docs[d][n]
                k_old = z[d][n]

                # Remove current assignment
                n_dk[d][k_old] -= 1
                n_kw[k_old][w] -= 1
                n_k[k_old] -= 1

                # Compute conditional probabilities
                probs = [0.0] * K
                for k in range(K):
                    probs[k] = (n_dk[d][k] + alpha) * (n_kw[k][w] + beta) / (n_k[k] + V_beta)

                # Normalise and sample
                total = sum(probs)
                if total > 0:
                    for k in range(K):
                        probs[k] /= total
                else:
                    # Uniform fallback (should not happen)
                    probs = [1.0 / K] * K

                r = rng.random()
                cumulative = 0.0
                k_new = K - 1
                for k in range(K):
                    cumulative += probs[k]
                    if r < cumulative:
                        k_new = k
                        break

                # Apply new assignment
                z[d][n] = k_new
                n_dk[d][k_new] += 1
                n_kw[k_new][w] += 1
                n_k[k_new] += 1

    return z, n_dk, n_kw, n_k


# ---------------------------------------------------------------------------
# Post-processing
# ---------------------------------------------------------------------------

def _extract_topics(n_kw, vocab, top_n=10):
    """Extract top words per topic with weights."""
    K = len(n_kw)
    topics = []
    for k in range(K):
        total = sum(n_kw[k])
        if total == 0:
            topics.append({"topic_id": k, "top_words": []})
            continue
        word_weights = []
        for w, count in enumerate(n_kw[k]):
            if count > 0:
                word_weights.append((vocab[w], count / total))
        word_weights.sort(key=lambda x: x[1], reverse=True)
        topics.append({
            "topic_id": k,
            "top_words": word_weights[:top_n],
        })
    return topics


def _study_topic_proportions(n_dk, study_ids, K, alpha):
    """Compute smoothed topic proportions for each study."""
    proportions = {}
    for d, sid in enumerate(study_ids):
        total = sum(n_dk[d]) + K * alpha
        if total == 0:
            proportions[sid] = [1.0 / K] * K
        else:
            proportions[sid] = [(n_dk[d][k] + alpha) / total for k in range(K)]
    return proportions


def _compute_perplexity(docs, n_dk, n_kw, n_k, K, alpha, beta, V):
    """Compute perplexity = exp(-1/N * sum(log P(w))).

    P(w_{d,n}) = sum_k theta_{d,k} * phi_{k,w}
    where theta and phi are estimated from counts.
    """
    V_beta = V * beta
    total_log = 0.0
    total_words = 0

    for d in range(len(docs)):
        doc_total = sum(n_dk[d]) + K * alpha
        if doc_total == 0:
            continue
        for n in range(len(docs[d])):
            w = docs[d][n]
            pw = 0.0
            for k in range(K):
                theta_dk = (n_dk[d][k] + alpha) / doc_total
                phi_kw = (n_kw[k][w] + beta) / (n_k[k] + V_beta)
                pw += theta_dk * phi_kw
            if pw > 0:
                total_log += math.log(pw)
            total_words += 1

    if total_words == 0:
        return float("inf")
    return math.exp(-total_log / total_words)


def _compute_coherence(topics, studies, top_n=10):
    """PMI-based topic coherence using study-level co-occurrence.

    For each pair of top words in a topic, compute:
        PMI(w1, w2) = log(P(w1,w2) / (P(w1)*P(w2)))
    where P is estimated from study-level occurrence.
    """
    # Build study-level word presence
    D = len(studies)
    if D == 0:
        return [0.0] * len(topics)

    study_words = []
    for s in studies:
        tokens = set(_tokenize(_study_text(s)))
        study_words.append(tokens)

    # Word document frequency
    word_df = {}
    for tokens in study_words:
        for w in tokens:
            word_df[w] = word_df.get(w, 0) + 1

    # Pair co-occurrence
    def pair_df(w1, w2):
        count = 0
        for tokens in study_words:
            if w1 in tokens and w2 in tokens:
                count += 1
        return count

    scores = []
    for topic in topics:
        words = [w for w, _ in topic["top_words"][:top_n]]
        if len(words) < 2:
            scores.append(0.0)
            continue
        pmi_sum = 0.0
        n_pairs = 0
        for i in range(len(words)):
            for j in range(i + 1, len(words)):
                w1, w2 = words[i], words[j]
                df1 = word_df.get(w1, 0)
                df2 = word_df.get(w2, 0)
                df12 = pair_df(w1, w2)
                if df1 > 0 and df2 > 0 and df12 > 0:
                    p1 = df1 / D
                    p2 = df2 / D
                    p12 = df12 / D
                    pmi_sum += math.log(p12 / (p1 * p2))
                n_pairs += 1
        scores.append(pmi_sum / n_pairs if n_pairs > 0 else 0.0)

    return scores


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_lda(studies, n_topics=3, alpha=0.1, beta=0.01, n_iter=200, seed=42):
    """Run simplified LDA on study texts.

    Args:
        studies: list of StudyInput
        n_topics: number of topics K
        alpha: Dirichlet prior on doc-topic distributions
        beta: Dirichlet prior on topic-word distributions
        n_iter: Gibbs sampling iterations
        seed: random seed for reproducibility

    Returns:
        dict with keys:
            topics: list of {topic_id, top_words: [(word, weight), ...]}
            study_topic_proportions: dict study_id -> list of floats
            perplexity: float
            coherence_scores: list of float (one per topic)
            n_topics: int
            n_iterations: int
    """
    if not studies:
        return {
            "topics": [],
            "study_topic_proportions": {},
            "perplexity": float("inf"),
            "coherence_scores": [],
            "n_topics": n_topics,
            "n_iterations": n_iter,
        }

    rng = random.Random(seed)
    K = n_topics

    docs, vocab, word2id = _build_corpus(studies)
    V = len(vocab)

    if V == 0:
        return {
            "topics": [],
            "study_topic_proportions": {s.study_id: [1.0 / K] * K for s in studies},
            "perplexity": float("inf"),
            "coherence_scores": [],
            "n_topics": K,
            "n_iterations": n_iter,
        }

    z, n_dk, n_kw, n_k = _gibbs_sample(docs, V, K, alpha, beta, n_iter, rng)

    study_ids = [s.study_id for s in studies]
    topics = _extract_topics(n_kw, vocab, top_n=10)
    proportions = _study_topic_proportions(n_dk, study_ids, K, alpha)
    perplexity = _compute_perplexity(docs, n_dk, n_kw, n_k, K, alpha, beta, V)
    coherence = _compute_coherence(topics, studies, top_n=10)

    return {
        "topics": topics,
        "study_topic_proportions": proportions,
        "perplexity": perplexity,
        "coherence_scores": coherence,
        "n_topics": K,
        "n_iterations": n_iter,
    }
