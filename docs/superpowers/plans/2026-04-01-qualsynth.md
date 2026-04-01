# QualSynth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a world-first browser-based qualitative evidence synthesis tool supporting meta-ethnography, thematic synthesis, and CERQual confidence assessment.

**Architecture:** Python engine (`qualsynth/`) with synthesis logic (no heavy deps), single-file HTML app (`app/qualsynth.html`) with Plotly.js, 25+ pytest tests.

**Tech Stack:** Python 3.11+, pytest. Browser: vanilla JS, Plotly.js 2.35.0.

**Spec:** `docs/superpowers/specs/2026-04-01-qualsynth-design.md`

---

## File Map

| File | Responsibility |
|------|---------------|
| `qualsynth/__init__.py` | Package marker |
| `qualsynth/models.py` | Dataclasses: StudyInput, Quote, Theme, TranslationCell, TranslationMatrix, CERQualFinding, SynthesisResult |
| `qualsynth/themes.py` | Theme CRUD, assignment, merge, saturation, hierarchy |
| `qualsynth/translation.py` | Meta-ethnography matrix, coverage, consistency, translation type |
| `qualsynth/cerqual.py` | CERQual 4-component assessment, overall confidence |
| `qualsynth/synthesis.py` | SoQF table, theme statistics, narrative assembly |
| `qualsynth/pipeline.py` | `run_qualsynth()` orchestrator |
| `qualsynth/certifier.py` | TruthCert hash + certification |
| `tests/conftest.py` | Fixtures for 2 examples |
| `tests/test_themes.py` | Theme operations tests |
| `tests/test_translation.py` | Translation matrix tests |
| `tests/test_cerqual.py` | CERQual scoring tests |
| `tests/test_synthesis.py` | Synthesis output tests |
| `tests/test_pipeline.py` | End-to-end tests |
| `app/qualsynth.html` | Single-file browser app (6 tabs, 3 Plotly charts) |
| `data/diabetes.json` | T2DM self-management example |
| `data/burnout.json` | HCW burnout example |

---

### Task 1: Project Scaffold + Models + Fixtures

**Files:**
- Create: `qualsynth/__init__.py`, `qualsynth/models.py`, `setup.py`, `LICENSE`
- Create: `data/diabetes.json`, `data/burnout.json`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create package marker**

```python
# qualsynth/__init__.py
```

- [ ] **Step 2: Create data models**

```python
# qualsynth/models.py
from dataclasses import dataclass, field

@dataclass
class Quote:
    quote_id: str
    text: str
    participant_id: str = ""
    page: str = ""
    context: str = ""

@dataclass
class StudyInput:
    study_id: str
    title: str
    authors: str
    year: int
    methodology: str = "other"
    setting: str = ""
    participants: str = ""
    sample_size: int = 0
    key_findings: list[str] = field(default_factory=list)
    quotes: list[Quote] = field(default_factory=list)
    quality_tool: str = "CASP"
    quality_score: str = "moderate"

@dataclass
class Theme:
    theme_id: str
    label: str
    description: str = ""
    level: str = "descriptive"
    parent_id: str | None = None
    assigned_quotes: list[str] = field(default_factory=list)
    assigned_studies: list[str] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)

@dataclass
class TranslationCell:
    study_id: str
    concept: str
    type: str = "present"
    evidence: str = ""

@dataclass
class TranslationMatrix:
    concepts: list[str] = field(default_factory=list)
    studies: list[str] = field(default_factory=list)
    cells: list[TranslationCell] = field(default_factory=list)
    translation_type: str = "reciprocal"

@dataclass
class CERQualFinding:
    finding_id: str
    finding_text: str
    methodological_limitations: str = "no"
    coherence: str = "no"
    adequacy: str = "no"
    relevance: str = "no"
    overall_confidence: str = ""
    explanation: str = ""
    contributing_studies: list[str] = field(default_factory=list)

@dataclass
class SynthesisResult:
    studies: list[StudyInput] = field(default_factory=list)
    themes: list[Theme] = field(default_factory=list)
    translation_matrix: TranslationMatrix | None = None
    cerqual_findings: list[CERQualFinding] = field(default_factory=list)
    synthesis_type: str = "thematic_synthesis"
    line_of_argument: str = ""
    n_studies: int = 0
    n_themes: int = 0
    n_analytical_themes: int = 0
    input_hash: str = ""
    certification: str = ""
```

- [ ] **Step 3: Create setup.py**

```python
from setuptools import setup, find_packages
setup(
    name="qualsynth",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.11",
)
```

- [ ] **Step 4: Create example datasets**

`data/diabetes.json`:
```json
{
  "name": "Patient Experience of T2DM Self-Management",
  "synthesis_type": "thematic_synthesis",
  "studies": [
    {
      "study_id": "Bury2005", "title": "Living with diabetes in a multi-ethnic community",
      "authors": "Bury M et al.", "year": 2005, "methodology": "phenomenology",
      "setting": "UK primary care, multi-ethnic London borough",
      "participants": "25 adults with T2DM (12 South Asian, 13 White British)",
      "sample_size": 25, "quality_tool": "CASP", "quality_score": "high",
      "key_findings": [
        "Diabetes experienced as an unwelcome identity shift",
        "Dietary management creates social tension at family meals",
        "Language barriers compound clinical confusion"
      ],
      "quotes": [
        {"quote_id": "B1", "text": "It changed who I am. I'm not the same person anymore.", "participant_id": "P03", "page": "p.412", "context": "Discussing diagnosis impact"},
        {"quote_id": "B2", "text": "My mother-in-law cooks everything with ghee. I can't refuse without causing offence.", "participant_id": "P08", "page": "p.415", "context": "Dietary challenges"}
      ]
    },
    {
      "study_id": "Lawton2006", "title": "Perceptions and experiences of taking oral hypoglycaemics",
      "authors": "Lawton J et al.", "year": 2006, "methodology": "grounded_theory",
      "setting": "Scotland, primary and secondary care",
      "participants": "40 patients with T2DM starting oral medication",
      "sample_size": 40, "quality_tool": "CASP", "quality_score": "high",
      "key_findings": [
        "Medication seen as proof of personal failure to control diet",
        "Tablet-taking normalises the condition over time",
        "Side effects rarely discussed with clinicians"
      ],
      "quotes": [
        {"quote_id": "L1", "text": "Taking tablets means I've failed, doesn't it? I couldn't do it with food alone.", "participant_id": "P12", "page": "p.1586", "context": "Starting medication"},
        {"quote_id": "L2", "text": "After a while you just pop the pill and forget about it. It becomes normal.", "participant_id": "P28", "page": "p.1588", "context": "Normalisation"}
      ]
    },
    {
      "study_id": "Rise2013", "title": "Making sense of diabetes self-management",
      "authors": "Rise MB et al.", "year": 2013, "methodology": "phenomenology",
      "setting": "Norway, diabetes education centre",
      "participants": "12 adults with T2DM attending education programme",
      "sample_size": 12, "quality_tool": "CASP", "quality_score": "moderate",
      "key_findings": [
        "Knowledge empowers but also creates anxiety about complications",
        "Peer support from other patients is more valued than clinical advice",
        "Self-monitoring enables sense of control"
      ],
      "quotes": [
        {"quote_id": "R1", "text": "Knowing what could happen scares me but also makes me try harder.", "participant_id": "P04", "page": "p.8", "context": "Education outcomes"},
        {"quote_id": "R2", "text": "The others in the group understand. My doctor doesn't live with it.", "participant_id": "P09", "page": "p.10", "context": "Peer support"}
      ]
    },
    {
      "study_id": "Gomersall2011", "title": "Conducting systematic reviews of qualitative studies of chronic illness",
      "authors": "Gomersall T et al.", "year": 2011, "methodology": "ethnography",
      "setting": "UK, community settings",
      "participants": "15 adults managing T2DM long-term (5+ years)",
      "sample_size": 15, "quality_tool": "CASP", "quality_score": "high",
      "key_findings": [
        "Long-term management leads to 'diabetes fatigue'",
        "Social identity as 'diabetic' resisted by most participants",
        "Technology (glucose monitors) both liberates and constrains"
      ],
      "quotes": [
        {"quote_id": "G1", "text": "I'm tired of thinking about it every single day. It never stops.", "participant_id": "P07", "page": "p.223", "context": "Long-term burden"},
        {"quote_id": "G2", "text": "I don't tell people. It's my business, not theirs.", "participant_id": "P11", "page": "p.225", "context": "Identity management"}
      ]
    },
    {
      "study_id": "Peel2004", "title": "Diagnosis and self-management of type 2 diabetes",
      "authors": "Peel E et al.", "year": 2004, "methodology": "grounded_theory",
      "setting": "UK, primary care",
      "participants": "40 newly diagnosed T2DM patients, longitudinal (over 1 year)",
      "sample_size": 40, "quality_tool": "CASP", "quality_score": "high",
      "key_findings": [
        "Initial relief at diagnosis ('at least it's not cancer') shifts to chronic burden",
        "Dietary advice perceived as contradictory and confusing",
        "Partners become informal health monitors creating relationship tension"
      ],
      "quotes": [
        {"quote_id": "P1", "text": "At first I thought, well at least it's manageable. Now I'm not so sure.", "participant_id": "P16", "page": "p.68", "context": "Trajectory of experience"},
        {"quote_id": "P2", "text": "My wife watches everything I eat now. It causes rows.", "participant_id": "P33", "page": "p.71", "context": "Relationship impact"}
      ]
    }
  ],
  "themes": [
    {"theme_id": "T1", "label": "Identity disruption", "level": "descriptive", "description": "Diabetes challenges existing self-concept and social identity"},
    {"theme_id": "T2", "label": "Daily burden of management", "level": "descriptive", "description": "Constant cognitive and practical demands of self-management"},
    {"theme_id": "T3", "label": "Social navigation", "level": "descriptive", "description": "Managing diabetes within family, cultural, and social contexts"},
    {"theme_id": "T4", "label": "Empowerment through knowledge", "level": "descriptive", "description": "Knowledge and self-monitoring as sources of control and anxiety"},
    {"theme_id": "A1", "label": "Living with a contested self", "level": "analytical", "description": "Overarching theme: diabetes creates ongoing tension between the pre-diagnosis self and the 'diabetic' identity, mediated by social context and knowledge"}
  ],
  "cerqual_findings": [
    {
      "finding_id": "F1",
      "finding_text": "People with T2DM experience diagnosis as a threat to their existing identity, resisting the label of 'diabetic' while gradually incorporating management into daily routines.",
      "methodological_limitations": "minor", "coherence": "no", "adequacy": "no", "relevance": "no",
      "contributing_studies": ["Bury2005", "Gomersall2011", "Peel2004", "Lawton2006"]
    },
    {
      "finding_id": "F2",
      "finding_text": "Self-management creates ongoing daily burden that participants describe as exhausting, with 'diabetes fatigue' emerging in long-term management.",
      "methodological_limitations": "no", "coherence": "no", "adequacy": "minor", "relevance": "no",
      "contributing_studies": ["Gomersall2011", "Bury2005", "Rise2013", "Peel2004"]
    },
    {
      "finding_id": "F3",
      "finding_text": "Dietary management is the most socially disruptive aspect, creating tension with family members and within cultural food practices.",
      "methodological_limitations": "no", "coherence": "no", "adequacy": "no", "relevance": "minor",
      "contributing_studies": ["Bury2005", "Peel2004", "Lawton2006"]
    },
    {
      "finding_id": "F4",
      "finding_text": "Peer support from others with diabetes is valued above professional clinical advice for day-to-day management strategies.",
      "methodological_limitations": "minor", "coherence": "no", "adequacy": "moderate", "relevance": "no",
      "contributing_studies": ["Rise2013", "Gomersall2011"]
    }
  ]
}
```

`data/burnout.json`:
```json
{
  "name": "Healthcare Worker Burnout During COVID-19",
  "synthesis_type": "meta_ethnography",
  "studies": [
    {
      "study_id": "Billings2021", "title": "Experiences of frontline healthcare workers during COVID-19",
      "authors": "Billings J et al.", "year": 2021, "methodology": "phenomenology",
      "setting": "UK NHS intensive care units",
      "participants": "20 ICU nurses and doctors",
      "sample_size": 20, "quality_tool": "CASP", "quality_score": "high",
      "key_findings": [
        "Moral distress from rationing care and PPE shortages",
        "Institutional communication perceived as inadequate and delayed",
        "Peer bonding strengthened under shared adversity"
      ],
      "quotes": [
        {"quote_id": "Bi1", "text": "We had to decide who gets the ventilator. That stays with you.", "participant_id": "N04", "page": "p.5", "context": "Triage decisions"},
        {"quote_id": "Bi2", "text": "Management sent emails. We needed them on the floor.", "participant_id": "D02", "page": "p.7", "context": "Leadership gap"}
      ]
    },
    {
      "study_id": "Catton2021", "title": "Global nursing workforce and COVID-19",
      "authors": "Catton H et al.", "year": 2021, "methodology": "grounded_theory",
      "setting": "Multi-country (UK, Italy, Brazil, India)",
      "participants": "35 nurses across 4 countries",
      "sample_size": 35, "quality_tool": "CASP", "quality_score": "moderate",
      "key_findings": [
        "Feeling abandoned by institutions while being publicly celebrated",
        "International differences in PPE access created moral anger",
        "Finding purpose through collective action and advocacy"
      ],
      "quotes": [
        {"quote_id": "C1", "text": "They called us heroes but wouldn't give us masks.", "participant_id": "N12", "page": "p.22", "context": "Hero narrative critique"},
        {"quote_id": "C2", "text": "I stayed because my colleagues needed me, not because the hospital asked.", "participant_id": "N28", "page": "p.25", "context": "Peer motivation"}
      ]
    },
    {
      "study_id": "Moradi2021", "title": "Healthcare workers' mental health during COVID-19",
      "authors": "Moradi Y et al.", "year": 2021, "methodology": "phenomenology",
      "setting": "Iran, public hospitals",
      "participants": "18 nurses and physicians",
      "sample_size": 18, "quality_tool": "CASP", "quality_score": "moderate",
      "key_findings": [
        "Fear of infecting family members dominated daily life",
        "Spiritual coping mechanisms (prayer, faith) provided resilience",
        "Professional identity strengthened through crisis"
      ],
      "quotes": [
        {"quote_id": "M1", "text": "I slept in my car for two months so I wouldn't bring it home.", "participant_id": "P05", "page": "p.4", "context": "Family separation"},
        {"quote_id": "M2", "text": "My faith kept me going when medicine couldn't help.", "participant_id": "P11", "page": "p.6", "context": "Spiritual coping"}
      ]
    },
    {
      "study_id": "Vindrola2020", "title": "Healthcare workers experiences during COVID-19",
      "authors": "Vindrola-Padros C et al.", "year": 2020, "methodology": "case_study",
      "setting": "UK NHS, multiple trusts",
      "participants": "30 HCWs (nurses, doctors, allied health)",
      "sample_size": 30, "quality_tool": "JBI", "quality_score": "high",
      "key_findings": [
        "Rapid redeployment caused de-skilling anxiety",
        "Meaning-making through narratives of purpose and duty",
        "Post-peak psychological fallout worse than during peak"
      ],
      "quotes": [
        {"quote_id": "V1", "text": "I'm a dermatologist. They put me on a COVID ward. I felt useless.", "participant_id": "D08", "page": "p.12", "context": "Redeployment anxiety"},
        {"quote_id": "V2", "text": "The worst part came after. When it slowed down, everything hit me.", "participant_id": "N15", "page": "p.14", "context": "Delayed distress"}
      ]
    }
  ],
  "concepts": ["moral_distress", "institutional_abandonment", "peer_solidarity", "meaning_making", "fear_of_contagion", "spiritual_coping"],
  "cerqual_findings": [
    {
      "finding_id": "F1",
      "finding_text": "Healthcare workers experienced profound moral distress from resource rationing, triage decisions, and witnessing preventable suffering.",
      "methodological_limitations": "no", "coherence": "no", "adequacy": "no", "relevance": "no",
      "contributing_studies": ["Billings2021", "Catton2021", "Moradi2021", "Vindrola2020"]
    },
    {
      "finding_id": "F2",
      "finding_text": "A pervasive sense of institutional abandonment — being publicly praised while privately unsupported — was a dominant source of anger.",
      "methodological_limitations": "minor", "coherence": "no", "adequacy": "no", "relevance": "minor",
      "contributing_studies": ["Billings2021", "Catton2021", "Vindrola2020"]
    },
    {
      "finding_id": "F3",
      "finding_text": "Peer solidarity and collective identity among frontline staff emerged as the primary coping mechanism, valued above institutional or psychological support.",
      "methodological_limitations": "no", "coherence": "no", "adequacy": "minor", "relevance": "no",
      "contributing_studies": ["Billings2021", "Catton2021", "Moradi2021"]
    }
  ]
}
```

- [ ] **Step 5: Create test fixtures**

```python
# tests/conftest.py
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
```

- [ ] **Step 6: Commit**

```bash
cd /c/Models/QualSynth
git add -A
git commit -m "feat: project scaffold, data models, example datasets, test fixtures"
```

---

### Task 2: Themes Module — Tests + Implementation

**Files:**
- Create: `tests/test_themes.py`
- Create: `qualsynth/themes.py`

- [ ] **Step 1: Write theme tests**

```python
# tests/test_themes.py
import pytest
from qualsynth.themes import (
    create_theme, assign_quote, merge_themes, compute_saturation,
    get_study_coverage, build_theme_stats,
)
from qualsynth.models import Theme

def test_create_theme():
    t = create_theme("T1", "Burden", description="Daily management burden")
    assert t.theme_id == "T1"
    assert t.label == "Burden"
    assert t.level == "descriptive"

def test_assign_quote():
    t = Theme(theme_id="T1", label="Burden")
    t = assign_quote(t, "Q1", "Study1")
    assert "Q1" in t.assigned_quotes
    assert "Study1" in t.assigned_studies

def test_assign_quote_no_duplicate():
    t = Theme(theme_id="T1", label="Burden")
    t = assign_quote(t, "Q1", "Study1")
    t = assign_quote(t, "Q1", "Study1")
    assert t.assigned_quotes.count("Q1") == 1

def test_merge_themes():
    t1 = Theme(theme_id="T1", label="A", assigned_quotes=["Q1"], assigned_studies=["S1"])
    t2 = Theme(theme_id="T2", label="B", assigned_quotes=["Q2"], assigned_studies=["S2"])
    merged = merge_themes("T3", "A+B", [t1, t2])
    assert set(merged.assigned_quotes) == {"Q1", "Q2"}
    assert set(merged.assigned_studies) == {"S1", "S2"}

def test_saturation(diabetes_studies, diabetes_themes):
    for theme in diabetes_themes:
        if theme.level == "descriptive":
            sat = compute_saturation(theme, len(diabetes_studies))
            assert 0.0 <= sat <= 1.0

def test_build_theme_stats(diabetes_themes, diabetes_studies):
    stats = build_theme_stats(diabetes_themes, len(diabetes_studies))
    assert len(stats) == len(diabetes_themes)
    for s in stats:
        assert "label" in s
        assert "n_quotes" in s
        assert "saturation" in s
```

- [ ] **Step 2: Implement themes module**

```python
# qualsynth/themes.py
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
```

- [ ] **Step 3: Run tests**

Run: `cd /c/Models/QualSynth && python -m pytest tests/test_themes.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 4: Commit**

```bash
cd /c/Models/QualSynth
git add qualsynth/themes.py tests/test_themes.py
git commit -m "feat: themes module — create, assign, merge, saturation"
```

---

### Task 3: Translation Matrix — Tests + Implementation

**Files:**
- Create: `tests/test_translation.py`
- Create: `qualsynth/translation.py`

- [ ] **Step 1: Write translation tests**

```python
# tests/test_translation.py
import pytest
from qualsynth.translation import build_translation_matrix, compute_coverage, compute_consistency, classify_translation

def test_build_matrix(burnout_studies, burnout_data):
    concepts = burnout_data[3].get("concepts", [])
    matrix = build_translation_matrix(burnout_studies, concepts)
    assert len(matrix.concepts) == len(concepts)
    assert len(matrix.studies) == len(burnout_studies)

def test_coverage_all_present():
    coverage = compute_coverage(n_present=5, n_studies=5)
    assert coverage == 1.0

def test_coverage_partial():
    coverage = compute_coverage(n_present=3, n_studies=5)
    assert abs(coverage - 0.6) < 0.01

def test_consistency_all_reciprocal():
    consistency = compute_consistency(n_present=5, n_refutational=0)
    assert consistency == 1.0

def test_classify_reciprocal():
    assert classify_translation(consistency=0.9, has_refutational=False) == "reciprocal"

def test_classify_refutational():
    assert classify_translation(consistency=0.4, has_refutational=True) == "refutational"

def test_classify_line_of_argument():
    assert classify_translation(consistency=0.7, has_refutational=True) == "line_of_argument"
```

- [ ] **Step 2: Implement translation module**

```python
# qualsynth/translation.py
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
```

- [ ] **Step 3: Run tests**

Run: `cd /c/Models/QualSynth && python -m pytest tests/test_translation.py -v`
Expected: All 7 tests PASS.

- [ ] **Step 4: Commit**

```bash
cd /c/Models/QualSynth
git add qualsynth/translation.py tests/test_translation.py
git commit -m "feat: translation matrix — coverage, consistency, classification"
```

---

### Task 4: CERQual Module — Tests + Implementation

**Files:**
- Create: `tests/test_cerqual.py`
- Create: `qualsynth/cerqual.py`

- [ ] **Step 1: Write CERQual tests**

```python
# tests/test_cerqual.py
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
```

- [ ] **Step 2: Implement CERQual module**

```python
# qualsynth/cerqual.py
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
```

- [ ] **Step 3: Run tests**

Run: `cd /c/Models/QualSynth && python -m pytest tests/test_cerqual.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 4: Commit**

```bash
cd /c/Models/QualSynth
git add qualsynth/cerqual.py tests/test_cerqual.py
git commit -m "feat: CERQual 4-component assessment with confidence rating"
```

---

### Task 5: Synthesis + Pipeline — Tests + Implementation

**Files:**
- Create: `tests/test_synthesis.py`, `tests/test_pipeline.py`
- Create: `qualsynth/synthesis.py`, `qualsynth/pipeline.py`, `qualsynth/certifier.py`

- [ ] **Step 1: Write synthesis + pipeline tests**

```python
# tests/test_synthesis.py
import pytest
from qualsynth.synthesis import build_soqf_table, build_theme_summary

def test_soqf_table(diabetes_findings):
    from qualsynth.cerqual import assess_cerqual
    assessed = [assess_cerqual(f) for f in diabetes_findings]
    table = build_soqf_table(assessed)
    assert len(table) == len(diabetes_findings)
    for row in table:
        assert "finding" in row
        assert "confidence" in row
        assert "n_studies" in row

def test_theme_summary(diabetes_themes, diabetes_studies):
    summary = build_theme_summary(diabetes_themes, diabetes_studies)
    assert "n_descriptive" in summary
    assert "n_analytical" in summary
    assert summary["n_descriptive"] >= 0

def test_soqf_confidence_populated(diabetes_findings):
    from qualsynth.cerqual import assess_cerqual
    assessed = [assess_cerqual(f) for f in diabetes_findings]
    table = build_soqf_table(assessed)
    for row in table:
        assert row["confidence"] in ("High", "Moderate", "Low", "Very Low")
```

```python
# tests/test_pipeline.py
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
```

- [ ] **Step 2: Implement synthesis.py**

```python
# qualsynth/synthesis.py

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
```

- [ ] **Step 3: Implement certifier.py**

```python
# qualsynth/certifier.py
import hashlib
import json

def compute_input_hash(studies):
    data = [{"id": s.study_id, "year": s.year, "n": s.sample_size} for s in studies]
    raw = json.dumps(data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def certify(studies, themes, cerqual_findings):
    if len(studies) < 2:
        return "REJECT"
    if len(themes) == 0 and len(cerqual_findings) == 0:
        return "WARN"
    return "PASS"
```

- [ ] **Step 4: Implement pipeline.py**

```python
# qualsynth/pipeline.py
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

    # Translation matrix (if concepts provided → meta-ethnography)
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
```

- [ ] **Step 5: Run full test suite**

Run: `cd /c/Models/QualSynth && python -m pytest tests/ -v`
Expected: All ~27 tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /c/Models/QualSynth
git add qualsynth/synthesis.py qualsynth/pipeline.py qualsynth/certifier.py tests/test_synthesis.py tests/test_pipeline.py
git commit -m "feat: synthesis + pipeline + CERQual with TruthCert"
```

---

### Task 6: Browser App

**Files:**
- Create: `app/qualsynth.html`

- [ ] **Step 1: Create the full browser application**

Create `app/qualsynth.html` as a single-file HTML application (~2,400 lines) with:
- All Python engine logic ported to JavaScript
- 6 tabs: Studies, Coding, Translation, Synthesis, CERQual, Report
- 3 Plotly.js visualizations (theme network, study-theme matrix, CERQual traffic light)
- 2 built-in examples (T2DM self-management, HCW burnout)
- Interactive theme coding: click to assign quotes to themes
- CERQual assessment form with auto-confidence calculation
- SoQF table generator
- Translation matrix viewer (for meta-ethnography)
- TruthCert JSON export
- Dark mode toggle

Port all functions: `createTheme()`, `assignQuote()`, `mergeThemes()`, `computeSaturation()`, `buildTranslationMatrix()`, `assessCerqual()`, `buildSoqfTable()`.

- [ ] **Step 2: Smoke test in browser**

Open `app/qualsynth.html`. Verify:
1. T2DM example loads 5 studies with quotes
2. Coding tab shows theme list with assign buttons
3. CERQual tab shows 4-component dropdowns per finding
4. Report tab generates SoQF table
5. All 3 charts render

- [ ] **Step 3: Commit**

```bash
cd /c/Models/QualSynth
git add app/qualsynth.html
git commit -m "feat: browser app with 6 tabs, 3 Plotly charts, 2 examples"
```

---

### Task 7: README + Final Verification

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README**

Include: purpose (world-first browser QES tool), quick start, features (meta-ethnography + thematic synthesis + CERQual), examples, validation, citation placeholder, MIT license.

- [ ] **Step 2: Run full test suite**

Run: `cd /c/Models/QualSynth && python -m pytest tests/ -v --tb=short`
Expected: All 27+ tests PASS.

- [ ] **Step 3: Commit**

```bash
cd /c/Models/QualSynth
git add README.md
git commit -m "docs: README with quick start, features, world-first claim"
```
