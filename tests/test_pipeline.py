import pytest
from qualsynth.pipeline import run_qualsynth
from qualsynth.models import SynthesisResult


def test_pipeline_returns_result(diabetes_data):
    studies, themes, findings, raw = diabetes_data
    result = run_qualsynth(studies, themes=themes, cerqual_findings=findings)
    assert isinstance(result, SynthesisResult)


def test_pipeline_themes_populated(diabetes_data):
    studies, themes, findings, raw = diabetes_data
    result = run_qualsynth(studies, themes=themes, cerqual_findings=findings)
    assert result.n_themes == len(themes)


def test_pipeline_cerqual_assessed(diabetes_data):
    studies, themes, findings, raw = diabetes_data
    result = run_qualsynth(studies, themes=themes, cerqual_findings=findings)
    assert len(result.cerqual_findings) == len(findings)
    for f in result.cerqual_findings:
        assert f.overall_confidence in ("High", "Moderate", "Low", "Very Low")


def test_pipeline_certification(diabetes_data):
    studies, themes, findings, raw = diabetes_data
    result = run_qualsynth(studies, themes=themes, cerqual_findings=findings)
    assert result.certification in ("PASS", "WARN", "REJECT")


def test_pipeline_burnout(burnout_data):
    studies, themes, findings, raw = burnout_data
    concepts = raw.get("concepts", [])
    result = run_qualsynth(studies, themes=themes, cerqual_findings=findings, concepts=concepts)
    assert isinstance(result, SynthesisResult)
    assert result.n_studies == len(studies)
