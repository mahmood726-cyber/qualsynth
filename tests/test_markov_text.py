import pytest
from qualsynth.models import StudyInput, Quote, Theme
from qualsynth.markov_text import generate_markov_narrative


@pytest.fixture
def markov_studies():
    """Studies with rich text content for Markov model training."""
    return [
        StudyInput(
            study_id="S1", title="Study 1", authors="A", year=2020,
            key_findings=[
                "Patients reported significant benefit from the intervention.",
                "Social support improved outcomes across all groups.",
                "Barriers to adherence included cost and complexity.",
            ],
            quotes=[
                Quote(quote_id="Q1", text="The programme really helped me feel better."),
                Quote(quote_id="Q2", text="Cost was a major barrier for many patients."),
            ],
        ),
        StudyInput(
            study_id="S2", title="Study 2", authors="B", year=2021,
            key_findings=[
                "Effective communication facilitated better engagement.",
                "Participants described the challenge of daily management.",
                "Support from peers enabled positive behaviour change.",
            ],
            quotes=[
                Quote(quote_id="Q3", text="Talking to others who understand makes a difference."),
                Quote(quote_id="Q4", text="Every day is a challenge but support helps."),
            ],
        ),
        StudyInput(
            study_id="S3", title="Study 3", authors="C", year=2022,
            key_findings=[
                "The intervention improved quality of life substantially.",
                "Negative experiences were reported by a minority.",
                "Benefit was most pronounced in the support group.",
            ],
            quotes=[
                Quote(quote_id="Q5", text="My life improved after joining the programme."),
            ],
        ),
    ]


@pytest.fixture
def markov_themes():
    """Themes for conditioned generation."""
    return [
        Theme(theme_id="T1", label="Benefits",
              assigned_studies=["S1", "S3"]),
        Theme(theme_id="T2", label="Barriers",
              assigned_studies=["S1", "S2"]),
    ]


def test_generated_text_non_empty(markov_studies):
    """Generated text must be a non-empty string."""
    result = generate_markov_narrative(markov_studies)
    assert isinstance(result["generated_text"], str)
    assert len(result["generated_text"]) > 0


def test_bigram_vocab_positive(markov_studies):
    """Bigram vocabulary must contain at least some words."""
    result = generate_markov_narrative(markov_studies)
    assert result["bigram_vocab_size"] > 0


def test_perplexity_positive(markov_studies):
    """Perplexity must be a positive finite number for real data."""
    result = generate_markov_narrative(markov_studies)
    assert result["perplexity"] > 0
    assert result["perplexity"] < float('inf')


def test_coherence_in_range(markov_studies):
    """Coherence score must be in [0, 1]."""
    result = generate_markov_narrative(markov_studies)
    assert 0.0 <= result["coherence_score"] <= 1.0


def test_theme_texts_generated(markov_studies, markov_themes):
    """Theme-conditioned texts must be generated for each theme with studies."""
    result = generate_markov_narrative(markov_studies, themes=markov_themes)
    assert "T1" in result["theme_texts"]
    assert "T2" in result["theme_texts"]
    # At least one theme should produce non-empty text
    has_text = any(len(t) > 0 for t in result["theme_texts"].values())
    assert has_text
