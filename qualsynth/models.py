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
