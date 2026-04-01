from qualsynth.models import Theme


def create_theme(theme_id, label, description="", level="descriptive", parent_id=None):
    return Theme(
        theme_id=theme_id,
        label=label,
        description=description,
        level=level,
        parent_id=parent_id,
    )


def assign_quote(theme, quote_id, study_id):
    quotes = list(theme.assigned_quotes)
    studies = list(theme.assigned_studies)
    if quote_id not in quotes:
        quotes.append(quote_id)
    if study_id not in studies:
        studies.append(study_id)
    return Theme(
        theme_id=theme.theme_id,
        label=theme.label,
        description=theme.description,
        level=theme.level,
        parent_id=theme.parent_id,
        assigned_quotes=quotes,
        assigned_studies=studies,
        concepts=list(theme.concepts),
    )


def merge_themes(new_id, new_label, themes):
    all_quotes = []
    all_studies = []
    all_concepts = []
    for t in themes:
        for q in t.assigned_quotes:
            if q not in all_quotes:
                all_quotes.append(q)
        for s in t.assigned_studies:
            if s not in all_studies:
                all_studies.append(s)
        for c in t.concepts:
            if c not in all_concepts:
                all_concepts.append(c)
    return Theme(
        theme_id=new_id,
        label=new_label,
        assigned_quotes=all_quotes,
        assigned_studies=all_studies,
        concepts=all_concepts,
    )


def compute_saturation(theme, n_total_studies):
    if n_total_studies <= 0:
        return 0.0
    return len(theme.assigned_studies) / n_total_studies


def get_study_coverage(themes):
    coverage = {}
    for t in themes:
        for sid in t.assigned_studies:
            if sid not in coverage:
                coverage[sid] = []
            coverage[sid].append(t.theme_id)
    return coverage


def build_theme_stats(themes, n_total_studies):
    stats = []
    for t in themes:
        stats.append({
            "theme_id": t.theme_id,
            "label": t.label,
            "level": t.level,
            "n_quotes": len(t.assigned_quotes),
            "n_studies": len(t.assigned_studies),
            "saturation": round(compute_saturation(t, n_total_studies), 2),
        })
    return stats
