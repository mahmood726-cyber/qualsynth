import pytest
from qualsynth.models import StudyInput, Quote, Theme
from qualsynth.sentiment import analyse_sentiment


@pytest.fixture
def sentiment_studies():
    """Studies with positive, negative, and mixed sentiment text."""
    return [
        StudyInput(
            study_id="S1", title="Benefits of peer support",
            authors="Smith A", year=2020, methodology="phenomenology",
            key_findings=[
                "Peer support was effective and improved wellbeing.",
                "Participants felt empowerment and confidence.",
            ],
            quotes=[
                Quote(quote_id="Q1", text="I feel hope and comfort from the group."),
            ],
        ),
        StudyInput(
            study_id="S2", title="Barriers to care",
            authors="Jones B", year=2021, methodology="grounded_theory",
            key_findings=[
                "Patients reported anxiety and frustration with the system.",
                "Isolation and stigma were difficult barriers.",
            ],
            quotes=[
                Quote(quote_id="Q2", text="The pain and burden are overwhelming."),
            ],
        ),
        StudyInput(
            study_id="S3", title="Mixed experience of treatment",
            authors="Lee C", year=2022, methodology="phenomenology",
            key_findings=[
                "Treatment was not effective for reducing pain.",
                "Some patients found hope despite the struggle.",
            ],
            quotes=[
                Quote(quote_id="Q3", text="I never felt comfort during the process."),
            ],
        ),
    ]


@pytest.fixture
def sentiment_themes():
    """Themes assigned to the sentiment studies."""
    return [
        Theme(theme_id="T1", label="Peer support",
              assigned_studies=["S1", "S3"]),
        Theme(theme_id="T2", label="System barriers",
              assigned_studies=["S2"]),
        Theme(theme_id="T3", label="Coping mechanisms",
              assigned_studies=["S1", "S2", "S3"]),
    ]


def test_study_sentiments_in_range(sentiment_studies, sentiment_themes):
    """All study-level sentiments must be in [-1, 1]."""
    result = analyse_sentiment(sentiment_studies, sentiment_themes)
    for sid, score in result["study_sentiments"].items():
        assert -1.0 - 1e-9 <= score <= 1.0 + 1e-9, (
            f"Study sentiment {score} out of range for {sid}"
        )


def test_positive_study_higher_than_negative(sentiment_studies, sentiment_themes):
    """The clearly positive study should score higher than the clearly negative one."""
    result = analyse_sentiment(sentiment_studies, sentiment_themes)
    assert result["study_sentiments"]["S1"] > result["study_sentiments"]["S2"], (
        "Positive study S1 should have higher sentiment than negative study S2"
    )


def test_theme_sentiments_in_range(sentiment_studies, sentiment_themes):
    """All theme-level sentiments must be in [-1, 1]."""
    result = analyse_sentiment(sentiment_studies, sentiment_themes)
    for tid, score in result["theme_sentiments"].items():
        assert -1.0 - 1e-9 <= score <= 1.0 + 1e-9, (
            f"Theme sentiment {score} out of range for {tid}"
        )


def test_overall_sentiment_in_range(sentiment_studies, sentiment_themes):
    """Overall sentiment must be in [-1, 1]."""
    result = analyse_sentiment(sentiment_studies, sentiment_themes)
    overall = result["overall_sentiment"]
    assert -1.0 - 1e-9 <= overall <= 1.0 + 1e-9, (
        f"Overall sentiment {overall} out of range"
    )


def test_emotion_profile_non_negative(sentiment_studies, sentiment_themes):
    """All emotion counts must be non-negative integers."""
    result = analyse_sentiment(sentiment_studies, sentiment_themes)
    profile = result["emotion_profile"]
    assert isinstance(profile, dict)
    for emotion, count in profile.items():
        assert isinstance(count, int) and count >= 0, (
            f"Emotion {emotion} count {count} is not a non-negative int"
        )
