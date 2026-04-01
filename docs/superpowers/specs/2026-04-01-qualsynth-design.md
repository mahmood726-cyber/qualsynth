# QualSynth — Qualitative Evidence Synthesis Engine

**Date**: 2026-04-01
**Status**: Approved
**Target Journal**: BMC Medical Research Methodology
**Location**: `C:\Models\QualSynth\`

## Summary

World-first browser-based tool for qualitative evidence synthesis. Supports meta-ethnography (Noblit & Hare 1988), thematic synthesis (Thomas & Harden 2008), and CERQual confidence assessment (Lewin et al. 2018). No existing browser tool handles any of these — current practice uses Word/Excel/NVivo.

## Architecture

- **Python engine** (`qualsynth/`): Data structures + synthesis logic, no heavy dependencies
- **Browser app** (`app/qualsynth.html`): Single-file HTML, interactive drag-and-drop coding UI
- **Test suite** (`tests/`): pytest, 25+ tests
- **TruthCert**: Hash-linked provenance

## Data Model

### StudyInput
```python
@dataclass
class StudyInput:
    study_id: str               # e.g. "Smith2020"
    title: str
    authors: str
    year: int
    methodology: str            # "phenomenology"/"grounded_theory"/"ethnography"/"case_study"/"other"
    setting: str                # e.g. "UK primary care"
    participants: str           # e.g. "20 adults with T2DM"
    sample_size: int
    key_findings: list[str]     # verbatim finding statements
    quotes: list[Quote]         # extracted participant quotes
    quality_tool: str           # "CASP"/"JBI"/"other"
    quality_score: str          # "high"/"moderate"/"low"
```

### Quote
```python
@dataclass
class Quote:
    quote_id: str
    text: str                   # verbatim quote
    participant_id: str         # optional participant label
    page: str                   # page/paragraph reference
    context: str                # surrounding context
```

### Theme
```python
@dataclass
class Theme:
    theme_id: str
    label: str                  # short name
    description: str            # full definition
    level: str                  # "descriptive" or "analytical"
    parent_id: str | None       # for hierarchy (analytical themes contain descriptive)
    assigned_quotes: list[str]  # quote_ids
    assigned_studies: list[str] # study_ids contributing
    concepts: list[str]         # concept labels from meta-ethnography
```

### TranslationMatrix
```python
@dataclass
class TranslationCell:
    study_id: str
    concept: str                # concept label
    type: str                   # "present"/"absent"/"refutational"/"partial"
    evidence: str               # supporting quote or finding reference

@dataclass
class TranslationMatrix:
    concepts: list[str]         # column headers
    studies: list[str]          # row headers
    cells: list[TranslationCell]
    translation_type: str       # "reciprocal"/"refutational"/"line_of_argument"
```

### CERQualAssessment
```python
@dataclass
class CERQualFinding:
    finding_id: str
    finding_text: str           # the review finding being assessed
    methodological_limitations: str  # "no"/"minor"/"moderate"/"serious"
    coherence: str              # "no"/"minor"/"moderate"/"serious"
    adequacy: str               # "no"/"minor"/"moderate"/"serious"
    relevance: str              # "no"/"minor"/"moderate"/"serious"
    overall_confidence: str     # "High"/"Moderate"/"Low"/"Very Low"
    explanation: str            # justification text
    contributing_studies: list[str]
```

### SynthesisResult
```python
@dataclass
class SynthesisResult:
    studies: list[StudyInput]
    themes: list[Theme]
    translation_matrix: TranslationMatrix | None
    cerqual_findings: list[CERQualFinding]
    synthesis_type: str         # "meta_ethnography"/"thematic_synthesis"
    line_of_argument: str       # narrative text
    n_studies: int
    n_themes: int
    n_analytical_themes: int
    certification: dict
```

## Methods

### 1. Meta-Ethnography (Noblit & Hare 1988)

Seven-phase process:
1. **Getting started** — define scope (handled by study input)
2. **Deciding what is relevant** — study selection (handled by study input)
3. **Reading the studies** — extract key concepts and quotes
4. **Determining how studies relate** — build translation matrix:
   - List key concepts across all studies (columns)
   - For each study (row), mark concept as present/absent/partial/refutational
5. **Translating studies into one another**:
   - **Reciprocal translation**: concepts are similar across studies → map equivalences
   - **Refutational translation**: concepts contradict → document the contradiction
6. **Synthesizing translations** — merge translated concepts into higher-order themes
7. **Expressing the synthesis** — line-of-argument narrative

**Translation matrix computation**:
- Coverage score: `concept_coverage = n_studies_with_concept / n_studies`
- Consistency: `concept_consistency = (n_present - n_refutational) / n_present` if n_present > 0
- Translation type decision:
  - If all concepts reciprocal (consistency > 0.8): "reciprocal"
  - If any refutational (consistency < 0.5): "refutational"
  - If mixed with a clear overarching narrative: "line_of_argument"

### 2. Thematic Synthesis (Thomas & Harden 2008)

Three-stage process:
1. **Line-by-line coding** — code each finding/quote to initial codes
2. **Descriptive themes** — group codes into descriptive themes (bottom-up)
3. **Analytical themes** — generate analytical themes that go beyond primary studies (interpretive leap)

**Implementation**:
- User creates themes and assigns quotes/findings to them
- Themes have parent/child hierarchy (descriptive under analytical)
- Auto-compute: studies per theme, quotes per theme, cross-study coverage
- Theme saturation indicator: `saturation = n_studies_contributing / n_total_studies`

### 3. CERQual (Confidence in the Evidence from Reviews of Qualitative Research)

Four components assessed per review finding:

| Component | Question | Levels |
|-----------|----------|--------|
| **Methodological limitations** | Do the studies have methodological concerns? | no/minor/moderate/serious |
| **Coherence** | How well does the data support the finding? | no/minor/moderate/serious |
| **Adequacy** | Is there enough data (richness + quantity)? | no/minor/moderate/serious |
| **Relevance** | How applicable are the studies to the review question? | no/minor/moderate/serious |

**Overall confidence** (starts at High, downgrade):
- No concerns in any component → High
- Minor concerns in 1-2 components → Moderate
- Moderate concerns or minor in 3+ → Low
- Serious concerns in any component → Very Low

**Computation**:
```
concern_weights = {"no": 0, "minor": 1, "moderate": 2, "serious": 3}
total_concern = sum(weights for all 4 components)
if total_concern == 0: "High"
elif total_concern <= 2: "Moderate"
elif total_concern <= 4 and max_concern < 3: "Low"
else: "Very Low"
```

### 4. Summary of Qualitative Findings (SoQF) Table

Standard table format:
| Finding | CERQual | Studies | Explanation |
|---------|---------|---------|-------------|
| Finding text | High/Mod/Low/VLow | n contributing | Justification |

## Browser App Tabs (6)

### Tab 1: Studies
- Add study form: title, authors, year, methodology, setting, participants, sample size
- Add key findings (free text, one per line)
- Add quotes with participant ID and page reference
- Quality assessment: tool + overall rating
- Study table with edit/delete
- Import JSON batch

### Tab 2: Coding
- Left panel: study findings/quotes (filterable by study)
- Right panel: theme tree (analytical → descriptive hierarchy)
- Create/rename/merge/split themes
- Assign quotes to themes via click (or drag in future)
- Theme card shows: label, description, assigned quote count, study count
- Theme saturation badge (% of studies contributing)
- Color-coded by coverage level

### Tab 3: Translation (Meta-ethnography)
- Concept columns (auto-populated from themes, editable)
- Study rows
- Cell editor: present/absent/partial/refutational + evidence text
- Auto-compute: coverage score, consistency, translation type badge
- Highlight refutational cells in red

### Tab 4: Synthesis
- Toggle: meta-ethnography view / thematic synthesis view
- Meta-ethnography: line-of-argument text editor with concept references
- Thematic synthesis: analytical theme builder (group descriptive themes)
- Theme network visualization (Plotly): nodes = themes, edges = shared studies
- Study-theme matrix visualization: heatmap of which studies contribute to which themes

### Tab 5: CERQual
- Per-finding assessment form (4 dropdowns + explanation text)
- Auto-suggested contributing studies based on theme assignments
- Confidence badge per finding
- Summary statistics: n findings at each confidence level

### Tab 6: Report
- Summary of Qualitative Findings (SoQF) table
- Structured methods paragraph
- Theme descriptions with supporting quotes
- Translation matrix (if meta-ethnography)
- CERQual justification table
- TruthCert JSON bundle

## Visualizations (3 Plotly charts)

1. **Theme network**: Force-directed graph, nodes = themes (size = quote count), edges = shared studies
2. **Study-theme matrix**: Heatmap, studies (rows) × themes (columns), color = quote count
3. **CERQual traffic light**: Grid of findings × 4 components, colored cells (green/amber/red)

## Built-in Examples

### 1. Patient Experience of Type 2 Diabetes Self-Management (5 studies)
- Phenomenological and grounded theory studies
- Themes: "daily burden", "identity threat", "social navigation", "empowerment through knowledge"
- CERQual: mostly Moderate confidence

### 2. Healthcare Worker Burnout During COVID-19 (4 studies)
- Ethnographic and interview studies
- Themes: "moral distress", "institutional abandonment", "peer solidarity", "meaning-making"
- CERQual: mixed (some Low due to adequacy)

## Test Coverage (25+ tests)

### themes.py (6 tests)
- Create/assign/merge themes
- Theme saturation calculation
- Hierarchy (descriptive under analytical)
- Quote assignment tracking

### translation.py (5 tests)
- Matrix construction from studies + concepts
- Coverage score computation
- Consistency score computation
- Translation type classification
- Refutational cell detection

### cerqual.py (6 tests)
- All "no" concerns → High
- Minor concerns → Moderate
- Serious concern → Very Low
- Boundary cases
- Contributing study linkage

### synthesis.py (4 tests)
- SoQF table generation
- Theme statistics (n studies, n quotes per theme)
- Line-of-argument text assembly
- Cross-study coverage matrix

### pipeline.py (4+ tests)
- End-to-end on each example
- Certification
- All components populated

## File Structure

```
C:\Models\QualSynth\
  qualsynth/
    __init__.py
    models.py           # All dataclasses
    themes.py            # Theme creation, assignment, merge, saturation
    translation.py       # Meta-ethnography translation matrix
    cerqual.py           # CERQual 4-component assessment
    synthesis.py         # SoQF table, theme stats, narrative
    pipeline.py          # run_qualsynth() orchestrator
    certifier.py         # TruthCert
  tests/
    conftest.py
    test_themes.py
    test_translation.py
    test_cerqual.py
    test_synthesis.py
    test_pipeline.py
  app/
    qualsynth.html       # Single-file browser app
  data/
    diabetes.json
    burnout.json
  setup.py
  README.md
  LICENSE
```

## Out of Scope (v1)

- NVivo import/export
- AI-assisted coding (LLM theme suggestion)
- Framework synthesis (Ritchie & Spencer)
- Critical interpretive synthesis
- Realist synthesis
- Multi-language quote handling
- Audio/video data coding
