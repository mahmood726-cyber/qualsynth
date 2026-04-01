import json
import pytest
from qualsynth.models import StudyInput, Quote, Theme, CERQualFinding


def _load_example(path):
    with open(path) as f:
        data = json.load(f)
    studies = []
    for s in data["studies"]:
        quotes = [Quote(**q) for q in s.get("quotes", [])]
        sd = dict(s)
        sd["quotes"] = quotes
        studies.append(StudyInput(**sd))
    themes = [Theme(**t) for t in data.get("themes", [])]
    findings = [CERQualFinding(**f) for f in data.get("cerqual_findings", [])]
    return studies, themes, findings, data


@pytest.fixture
def diabetes_data():
    return _load_example("data/diabetes.json")


@pytest.fixture
def burnout_data():
    return _load_example("data/burnout.json")


@pytest.fixture
def diabetes_studies(diabetes_data):
    return diabetes_data[0]


@pytest.fixture
def diabetes_themes(diabetes_data):
    return diabetes_data[1]


@pytest.fixture
def diabetes_findings(diabetes_data):
    return diabetes_data[2]


@pytest.fixture
def burnout_studies(burnout_data):
    return burnout_data[0]


@pytest.fixture
def burnout_findings(burnout_data):
    return burnout_data[2]
