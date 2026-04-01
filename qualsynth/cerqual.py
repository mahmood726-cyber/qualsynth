from qualsynth.models import CERQualFinding

CONCERN_WEIGHTS = {"no": 0, "minor": 1, "moderate": 2, "serious": 3}


def assess_cerqual(finding):
    components = [
        finding.methodological_limitations,
        finding.coherence,
        finding.adequacy,
        finding.relevance,
    ]
    weights = [CONCERN_WEIGHTS.get(c, 0) for c in components]
    total = sum(weights)
    max_concern = max(weights)

    if max_concern >= 3:
        confidence = "Very Low"
    elif max_concern >= 2:
        confidence = "Low"
    elif total >= 3:
        confidence = "Low"
    elif total == 0:
        confidence = "High"
    else:
        confidence = "Moderate"

    return CERQualFinding(
        finding_id=finding.finding_id,
        finding_text=finding.finding_text,
        methodological_limitations=finding.methodological_limitations,
        coherence=finding.coherence,
        adequacy=finding.adequacy,
        relevance=finding.relevance,
        overall_confidence=confidence,
        explanation=finding.explanation,
        contributing_studies=list(finding.contributing_studies),
    )
