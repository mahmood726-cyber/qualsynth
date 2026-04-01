import pytest
from qualsynth.cerqual import assess_cerqual
from qualsynth.models import CERQualFinding


def test_all_no_concerns_is_high():
    f = CERQualFinding(finding_id="F1", finding_text="test",
                        methodological_limitations="no", coherence="no",
                        adequacy="no", relevance="no")
    result = assess_cerqual(f)
    assert result.overall_confidence == "High"


def test_one_minor_is_moderate():
    f = CERQualFinding(finding_id="F1", finding_text="test",
                        methodological_limitations="minor", coherence="no",
                        adequacy="no", relevance="no")
    result = assess_cerqual(f)
    assert result.overall_confidence == "Moderate"


def test_two_minor_is_moderate():
    f = CERQualFinding(finding_id="F1", finding_text="test",
                        methodological_limitations="minor", coherence="minor",
                        adequacy="no", relevance="no")
    result = assess_cerqual(f)
    assert result.overall_confidence == "Moderate"


def test_one_moderate_concern_is_low():
    f = CERQualFinding(finding_id="F1", finding_text="test",
                        methodological_limitations="moderate", coherence="no",
                        adequacy="no", relevance="no")
    result = assess_cerqual(f)
    assert result.overall_confidence == "Low"


def test_serious_concern_is_very_low():
    f = CERQualFinding(finding_id="F1", finding_text="test",
                        methodological_limitations="serious", coherence="no",
                        adequacy="no", relevance="no")
    result = assess_cerqual(f)
    assert result.overall_confidence == "Very Low"


def test_three_minor_is_low():
    f = CERQualFinding(finding_id="F1", finding_text="test",
                        methodological_limitations="minor", coherence="minor",
                        adequacy="minor", relevance="no")
    result = assess_cerqual(f)
    assert result.overall_confidence == "Low"
