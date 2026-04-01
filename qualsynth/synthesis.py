def build_soqf_table(assessed_findings):
    table = []
    for f in assessed_findings:
        table.append({
            "finding_id": f.finding_id,
            "finding": f.finding_text,
            "confidence": f.overall_confidence,
            "n_studies": len(f.contributing_studies),
            "studies": list(f.contributing_studies),
            "explanation": f.explanation,
        })
    return table


def build_theme_summary(themes, studies):
    descriptive = [t for t in themes if t.level == "descriptive"]
    analytical = [t for t in themes if t.level == "analytical"]
    all_study_ids = {s.study_id for s in studies}
    covered = set()
    for t in themes:
        covered.update(t.assigned_studies)
    coverage = len(covered & all_study_ids) / len(all_study_ids) if all_study_ids else 0
    return {
        "n_descriptive": len(descriptive),
        "n_analytical": len(analytical),
        "n_total": len(themes),
        "study_coverage": round(coverage, 2),
        "descriptive_labels": [t.label for t in descriptive],
        "analytical_labels": [t.label for t in analytical],
    }
