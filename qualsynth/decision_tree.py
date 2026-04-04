"""Decision Tree Theme Classification.

Pure Python implementation. Builds TF-IDF feature vectors per study,
trains an ID3 decision tree (and random forest) to classify studies
into themes, and reports OOB error, feature importance, and LOO accuracy.
"""

import math
import random

from qualsynth.similarity import _tokenize


def _study_text(study):
    """Concatenate key_findings and quote texts for a study."""
    parts = list(study.key_findings)
    for q in study.quotes:
        parts.append(q.text)
    return " ".join(parts)


def _build_tfidf_vectors(studies, max_vocab=50):
    """Build TF-IDF vectors restricted to top-max_vocab words by document frequency.

    Returns:
        vectors: list of dicts {word: tfidf}
        vocab: sorted list of top words
    """
    doc_tokens_list = []
    df = {}
    for s in studies:
        tokens = _tokenize(_study_text(s))
        doc_tokens_list.append(tokens)
        seen = set(tokens)
        for t in seen:
            df[t] = df.get(t, 0) + 1

    # Pick top-max_vocab words by document frequency (break ties alphabetically)
    sorted_terms = sorted(df.keys(), key=lambda w: (-df[w], w))
    vocab = sorted_terms[:max_vocab]
    vocab_set = set(vocab)

    n_docs = len(studies)
    idf = {}
    for t in vocab:
        idf[t] = math.log(n_docs / (1 + df.get(t, 0)))

    vectors = []
    for tokens in doc_tokens_list:
        n_tokens = len(tokens)
        if n_tokens == 0:
            vectors.append({w: 0.0 for w in vocab})
            continue
        tf = {}
        for t in tokens:
            if t in vocab_set:
                tf[t] = tf.get(t, 0) + 1
        vec = {}
        for w in vocab:
            vec[w] = (tf.get(w, 0) / n_tokens) * idf.get(w, 0.0)
        vectors.append(vec)

    return vectors, sorted(vocab)


def _entropy(labels):
    """Shannon entropy of a label list."""
    if not labels:
        return 0.0
    counts = {}
    for l in labels:
        counts[l] = counts.get(l, 0) + 1
    n = len(labels)
    ent = 0.0
    for c in counts.values():
        p = c / n
        if p > 0:
            ent -= p * math.log2(p)
    return ent


def _majority(labels):
    """Return the most common label."""
    counts = {}
    for l in labels:
        counts[l] = counts.get(l, 0) + 1
    return max(counts, key=lambda k: counts[k])


class _TreeNode:
    """Internal node or leaf of an ID3 decision tree."""
    __slots__ = ('feature', 'threshold', 'left', 'right', 'label')

    def __init__(self, feature=None, threshold=None, left=None, right=None, label=None):
        self.feature = feature
        self.threshold = threshold
        self.left = left
        self.right = right
        self.label = label

    def predict(self, vec):
        if self.label is not None:
            return self.label
        val = vec.get(self.feature, 0.0)
        if val <= self.threshold:
            return self.left.predict(vec)
        else:
            return self.right.predict(vec)


def _build_id3(indices, vectors, labels, features, depth, max_depth, min_samples):
    """Recursively build an ID3 tree.

    Args:
        indices: list of sample indices to consider
        vectors: list of dicts {word: tfidf}
        labels: list of theme labels per sample
        features: list of feature names to consider
        depth: current depth
        max_depth: max tree depth
        min_samples: min samples to split
    """
    current_labels = [labels[i] for i in indices]

    # Base cases
    if len(set(current_labels)) == 1:
        return _TreeNode(label=current_labels[0])
    if depth >= max_depth or len(indices) < min_samples or not features:
        return _TreeNode(label=_majority(current_labels))

    parent_ent = _entropy(current_labels)
    best_gain = -1.0
    best_feature = None
    best_threshold = None
    best_left = None
    best_right = None

    for feat in features:
        values = [vectors[i].get(feat, 0.0) for i in indices]
        threshold = sorted(values)[len(values) // 2]  # median

        left_idx = [i for i in indices if vectors[i].get(feat, 0.0) <= threshold]
        right_idx = [i for i in indices if vectors[i].get(feat, 0.0) > threshold]

        if not left_idx or not right_idx:
            continue

        left_labels = [labels[i] for i in left_idx]
        right_labels = [labels[i] for i in right_idx]

        n = len(indices)
        weighted_ent = (len(left_idx) / n) * _entropy(left_labels) + \
                       (len(right_idx) / n) * _entropy(right_labels)
        gain = parent_ent - weighted_ent

        if gain > best_gain:
            best_gain = gain
            best_feature = feat
            best_threshold = threshold
            best_left = left_idx
            best_right = right_idx

    if best_feature is None or best_gain <= 0:
        return _TreeNode(label=_majority(current_labels))

    remaining_features = [f for f in features if f != best_feature]
    left_node = _build_id3(best_left, vectors, labels, remaining_features,
                           depth + 1, max_depth, min_samples)
    right_node = _build_id3(best_right, vectors, labels, remaining_features,
                            depth + 1, max_depth, min_samples)

    return _TreeNode(feature=best_feature, threshold=best_threshold,
                     left=left_node, right=right_node)


def _impurity_importance(node, vectors, labels, indices):
    """Compute mean impurity decrease per feature by traversing the tree."""
    importance = {}

    def _traverse(node, idx):
        if node.label is not None or not idx:
            return
        feat = node.feature
        thr = node.threshold
        left_idx = [i for i in idx if vectors[i].get(feat, 0.0) <= thr]
        right_idx = [i for i in idx if vectors[i].get(feat, 0.0) > thr]

        parent_labels = [labels[i] for i in idx]
        left_labels = [labels[i] for i in left_idx]
        right_labels = [labels[i] for i in right_idx]

        n = len(idx)
        if n == 0:
            return
        decrease = _entropy(parent_labels) - \
                   (len(left_idx) / n) * _entropy(left_labels) - \
                   (len(right_idx) / n) * _entropy(right_labels)

        importance[feat] = importance.get(feat, 0.0) + decrease * (n / len(vectors))

        _traverse(node.left, left_idx)
        _traverse(node.right, right_idx)

    _traverse(node, indices)
    return importance


def analyse_decision_tree(studies, themes, seed=42):
    """Decision tree + random forest theme classification.

    Args:
        studies: list of StudyInput
        themes: list of Theme (with assigned_studies)
        seed: random seed for bootstrap

    Returns:
        dict with keys:
            oob_error: float in [0, 1]
            feature_importance: dict {word: float}
            loo_accuracy: float in [0, 1]
            predictions: dict {study_id: theme_id}
            top_features: list of top-10 feature names
    """
    # Build study -> theme mapping (use first theme that claims the study)
    study_theme = {}
    for theme in themes:
        for sid in theme.assigned_studies:
            if sid not in study_theme:
                study_theme[sid] = theme.theme_id

    # Filter to studies that have a theme assignment
    indexed_studies = []
    labels = []
    for i, s in enumerate(studies):
        tid = study_theme.get(s.study_id)
        if tid is not None:
            indexed_studies.append(i)
            labels.append(tid)

    if not indexed_studies:
        return {
            "oob_error": 0.0,
            "feature_importance": {},
            "loo_accuracy": 0.0,
            "predictions": {},
            "top_features": [],
        }

    vectors, vocab = _build_tfidf_vectors(studies)
    n = len(indexed_studies)
    rng = random.Random(seed)

    # --- Single tree for predictions and LOO ---
    all_indices = list(range(n))
    tree = _build_id3(all_indices, [vectors[i] for i in indexed_studies],
                      labels, list(vocab), 0, 5, 2)

    # Predictions from single tree
    predictions = {}
    for j, idx in enumerate(indexed_studies):
        pred = tree.predict(vectors[idx])
        predictions[studies[idx].study_id] = pred

    # LOO accuracy
    loo_correct = 0
    for j in range(n):
        train_idx = [k for k in range(n) if k != j]
        train_labels = [labels[k] for k in train_idx]
        train_vectors = [vectors[indexed_studies[k]] for k in train_idx]

        if len(set(train_labels)) < 1:
            continue

        loo_tree = _build_id3(list(range(len(train_idx))), train_vectors,
                              train_labels, list(vocab), 0, 5, 2)
        pred = loo_tree.predict(vectors[indexed_studies[j]])
        if pred == labels[j]:
            loo_correct += 1

    loo_accuracy = loo_correct / n if n > 0 else 0.0

    # --- Random Forest (T=10 trees) ---
    n_trees = 10
    n_features = max(1, int(math.sqrt(len(vocab))))
    oob_predictions = {}  # study index -> list of predictions

    total_importance = {}
    for t in range(n_trees):
        # Bootstrap sample
        bootstrap = [rng.randint(0, n - 1) for _ in range(n)]
        oob_set = set(range(n)) - set(bootstrap)

        # Random feature subset
        shuffled_vocab = list(vocab)
        rng.shuffle(shuffled_vocab)
        feature_subset = shuffled_vocab[:n_features]

        bootstrap_vectors = [vectors[indexed_studies[k]] for k in bootstrap]
        bootstrap_labels = [labels[k] for k in bootstrap]

        rf_tree = _build_id3(list(range(len(bootstrap))), bootstrap_vectors,
                             bootstrap_labels, feature_subset, 0, 5, 2)

        # Feature importance from this tree
        imp = _impurity_importance(rf_tree, bootstrap_vectors, bootstrap_labels,
                                   list(range(len(bootstrap))))
        for feat, val in imp.items():
            total_importance[feat] = total_importance.get(feat, 0.0) + val

        # OOB predictions
        for j in oob_set:
            pred = rf_tree.predict(vectors[indexed_studies[j]])
            if j not in oob_predictions:
                oob_predictions[j] = []
            oob_predictions[j].append(pred)

    # Average feature importance
    feature_importance = {}
    for feat, val in total_importance.items():
        feature_importance[feat] = val / n_trees

    # OOB error
    oob_correct = 0
    oob_total = 0
    for j, preds in oob_predictions.items():
        if preds:
            # Majority vote
            counts = {}
            for p in preds:
                counts[p] = counts.get(p, 0) + 1
            majority = max(counts, key=lambda k: counts[k])
            if majority == labels[j]:
                oob_correct += 1
            oob_total += 1

    oob_error = 1.0 - (oob_correct / oob_total) if oob_total > 0 else 0.0

    # Top features
    sorted_features = sorted(feature_importance.items(), key=lambda x: -x[1])
    top_features = [f[0] for f in sorted_features[:10]]

    return {
        "oob_error": oob_error,
        "feature_importance": feature_importance,
        "loo_accuracy": loo_accuracy,
        "predictions": predictions,
        "top_features": top_features,
    }
