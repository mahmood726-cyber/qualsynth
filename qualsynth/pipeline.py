from qualsynth.models import SynthesisResult
from qualsynth.themes import build_theme_stats
from qualsynth.translation import build_translation_matrix, analyze_matrix
from qualsynth.cerqual import assess_cerqual
from qualsynth.synthesis import build_soqf_table, build_theme_summary
from qualsynth.certifier import compute_input_hash, certify


def run_qualsynth(studies, themes=None, cerqual_findings=None, concepts=None,
                  synthesis_type="thematic_synthesis"):
    if themes is None:
        themes = []
    if cerqual_findings is None:
        cerqual_findings = []

    # Assess CERQual
    assessed = [assess_cerqual(f) for f in cerqual_findings]

    # Translation matrix (if concepts provided -> meta-ethnography)
    trans_matrix = None
    if concepts:
        trans_matrix = build_translation_matrix(studies, concepts)
        synthesis_type = "meta_ethnography"

    # Theme stats
    theme_summary = build_theme_summary(themes, studies)

    # Certify
    input_hash = compute_input_hash(studies)
    cert = certify(studies, themes, cerqual_findings)

    return SynthesisResult(
        studies=studies,
        themes=themes,
        translation_matrix=trans_matrix,
        cerqual_findings=assessed,
        synthesis_type=synthesis_type,
        line_of_argument="",
        n_studies=len(studies),
        n_themes=len(themes),
        n_analytical_themes=theme_summary["n_analytical"],
        input_hash=input_hash,
        certification=cert,
    )
