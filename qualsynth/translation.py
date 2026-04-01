from qualsynth.models import TranslationMatrix, TranslationCell


def build_translation_matrix(studies, concepts):
    study_ids = [s.study_id for s in studies]
    cells = []
    for study in studies:
        findings_text = " ".join(study.key_findings).lower()
        for concept in concepts:
            concept_lower = concept.lower().replace("_", " ")
            if concept_lower in findings_text or any(concept_lower in q.text.lower() for q in study.quotes):
                cells.append(TranslationCell(study_id=study.study_id, concept=concept, type="present"))
            else:
                cells.append(TranslationCell(study_id=study.study_id, concept=concept, type="absent"))
    return TranslationMatrix(concepts=list(concepts), studies=study_ids, cells=cells)


def compute_coverage(n_present, n_studies):
    if n_studies <= 0:
        return 0.0
    return n_present / n_studies


def compute_consistency(n_present, n_refutational):
    if n_present <= 0:
        return 0.0
    return (n_present - n_refutational) / n_present


def classify_translation(consistency, has_refutational):
    if consistency >= 0.8 and not has_refutational:
        return "reciprocal"
    if consistency < 0.5:
        return "refutational"
    return "line_of_argument"


def analyze_matrix(matrix):
    concept_stats = {}
    for concept in matrix.concepts:
        cells_for_concept = [c for c in matrix.cells if c.concept == concept]
        n_present = sum(1 for c in cells_for_concept if c.type == "present")
        n_refutational = sum(1 for c in cells_for_concept if c.type == "refutational")
        n_studies = len(matrix.studies)
        coverage = compute_coverage(n_present, n_studies)
        consistency = compute_consistency(n_present, n_refutational)
        concept_stats[concept] = {
            "coverage": round(coverage, 3),
            "consistency": round(consistency, 3),
            "n_present": n_present,
            "n_refutational": n_refutational,
        }

    all_consistencies = [s["consistency"] for s in concept_stats.values() if s["n_present"] > 0]
    avg_consistency = sum(all_consistencies) / len(all_consistencies) if all_consistencies else 1.0
    has_refutational = any(s["n_refutational"] > 0 for s in concept_stats.values())
    translation_type = classify_translation(avg_consistency, has_refutational)

    return {
        "concept_stats": concept_stats,
        "overall_consistency": round(avg_consistency, 3),
        "translation_type": translation_type,
    }
