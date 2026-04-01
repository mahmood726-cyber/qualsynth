# QualSynth

World-first browser-based qualitative evidence synthesis tool supporting meta-ethnography (Noblit & Hare 1988), thematic synthesis (Thomas & Harden 2008), and CERQual confidence assessment (Lewin et al. 2018).

## Quick Start

### Browser App
Open `app/qualsynth.html` in any modern browser. No installation required.

### Python Engine
```bash
pip install -e .
python -c "from qualsynth.pipeline import run_qualsynth; print('OK')"
```

### Run Tests
```bash
python -m pytest tests/ -v
```

## Features

- **Meta-Ethnography**: Translation matrix with coverage/consistency scoring, reciprocal/refutational/line-of-argument classification
- **Thematic Synthesis**: Create, assign, merge themes with saturation tracking
- **CERQual Assessment**: 4-component (methodological limitations, coherence, adequacy, relevance) confidence rating
- **Summary of Qualitative Findings (SoQF) Table**: Standard output format
- **3 Plotly Visualizations**: Theme network, study-theme matrix, CERQual traffic light
- **2 Built-in Examples**: T2DM self-management (5 studies), HCW burnout during COVID-19 (4 studies)
- **TruthCert Export**: Hash-linked provenance bundle
- **Dark Mode**: WCAG AA accessible

## Architecture

```
qualsynth/          Python engine (no heavy dependencies)
  models.py         Dataclasses (StudyInput, Quote, Theme, CERQualFinding, etc.)
  themes.py         Theme CRUD, assignment, merge, saturation
  translation.py    Meta-ethnography translation matrix
  cerqual.py        CERQual 4-component assessment
  synthesis.py      SoQF table, theme statistics
  pipeline.py       run_qualsynth() orchestrator
  certifier.py      TruthCert hash + certification

app/
  qualsynth.html    Single-file browser app (all logic ported to JS)

data/
  diabetes.json     T2DM self-management example (5 studies)
  burnout.json      HCW burnout example (4 studies)

tests/              27 pytest tests
```

## Validation

All synthesis logic is implemented in both Python (testable) and JavaScript (interactive). The Python engine serves as the reference implementation with 27 automated tests covering themes, translation, CERQual, synthesis, and end-to-end pipeline.

## Citation

If you use QualSynth in your research, please cite:
> QualSynth: A browser-based tool for qualitative evidence synthesis. [Year]. Available at: [URL]

## License

MIT
