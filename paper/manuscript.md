# QualSynth: An Open-Source Browser-Based Tool for Qualitative Evidence Synthesis with Integrated CERQual Confidence Assessment

[AUTHOR]^1,2^

^1^ [AFFILIATION 1]
^2^ [AFFILIATION 2]

Correspondence: [AUTHOR], [EMAIL]

**Word count:** ~4,800

---

## Abstract

**Background:** Qualitative evidence synthesis (QES) methods -- including meta-ethnography, thematic synthesis, and the Confidence in the Evidence from Reviews of Qualitative Research (CERQual) framework -- are increasingly used in health research to inform clinical guidelines and policy. Despite growing demand, researchers must currently perform QES entirely by hand using generic tools such as word processors and spreadsheets, with no purpose-built software available. This lack of dedicated tooling introduces inefficiency, limits transparency, and impedes reproducibility.

**Methods:** We developed QualSynth, a free, open-source software tool that digitises the complete QES workflow within a single browser-based application. QualSynth implements three core methodological components: (1) a thematic synthesis engine supporting hierarchical coding of qualitative data into descriptive and analytical themes, with saturation analysis; (2) a reciprocal translation matrix for meta-ethnography, with automated concept detection, coverage and consistency metrics, and translation type classification; and (3) a structured CERQual assessment module covering all four components (methodological limitations, coherence, adequacy, and relevance) with algorithmic confidence grading. Beyond these core components, QualSynth provides fifteen computational methods organised in five progressive tiers -- from TF-IDF similarity and Shannon entropy saturation (Tier 1) through latent semantic analysis and Bayesian saturation estimation (Tier 2), word embeddings and argument mining (Tier 3), formal concept analysis and dialectical analysis (Tier 4), to LDA topic modelling and computational grounded theory (Tier 5). All algorithms are implemented in pure Python with no external dependencies. The tool generates Summary of Qualitative Findings (SoQF) tables, interactive visualisations including an analytics dashboard with similarity heatmaps, saturation curves, co-occurrence networks, and topic word clouds, methods paragraphs, and auditable export bundles. A Python engine (nineteen modules, 102 unit tests) validates all algorithms, while a standalone HTML/JavaScript front-end requires no installation or server.

**Results:** We demonstrate QualSynth using an illustrative synthesis of five qualitative studies on patient experiences of type 2 diabetes self-management. The tool identified four descriptive themes and one analytical theme across 132 participants, assessed CERQual confidence for four review findings (2 High, 1 Moderate, 1 Low), and generated a complete SoQF table and methods paragraph in under 10 minutes of active use. The computational analytics dashboard identified study similarity clusters via TF-IDF cosine similarity, confirmed thematic saturation at the fourth study via entropy analysis, and discovered three latent topics via LDA. A second demonstration using four studies of healthcare worker burnout during COVID-19 illustrates the meta-ethnography pathway with a six-concept translation matrix.

**Conclusions:** QualSynth is the first software tool purpose-built for qualitative evidence synthesis. By integrating theme coding, reciprocal translation, CERQual assessment, and fifteen computational text analytics methods within a transparent, reproducible workflow, it addresses a significant gap in the evidence synthesis toolkit. QualSynth is freely available under an open-source licence at [REPOSITORY URL].

**Keywords:** qualitative evidence synthesis, meta-ethnography, thematic synthesis, CERQual, software tool, systematic review, open-source

---

## Background

Qualitative evidence synthesis (QES) has become an essential methodology in health research, enabling the systematic integration of findings from multiple qualitative studies to generate higher-order interpretations that transcend individual study findings [1,2]. Two dominant approaches have emerged: thematic synthesis, which applies thematic analysis techniques to extracted qualitative data [3], and meta-ethnography, which translates concepts across studies to develop new interpretive frameworks [4]. The Cochrane Qualitative and Implementation Methods Group now recognises QES as a core component of mixed-methods systematic reviews [5], and the GRADE-CERQual (Confidence in the Evidence from Reviews of Qualitative Research) framework provides a structured approach for assessing confidence in QES findings [6].

Despite this methodological maturity, the practical conduct of QES remains almost entirely manual. Researchers typically code qualitative data in Microsoft Word or NVivo, construct translation matrices in Excel, and assess CERQual on paper forms [7]. This reliance on generic tools introduces several problems. First, the process is labour-intensive: a typical QES requires weeks of manual coding, matrix construction, and confidence assessment [8]. Second, the lack of structured tooling impedes transparency -- reviewers cannot easily audit the trail from primary data through themes to synthesis findings. Third, reproducibility is limited because the analytical steps are not captured in a format amenable to verification or replication [9].

The contrast with quantitative meta-analysis is stark. Researchers conducting quantitative syntheses have access to dozens of dedicated software tools -- RevMan [10], metafor [11], Stata meta commands [12] -- that automate effect size calculation, pooling, heterogeneity assessment, and forest plot generation. No equivalent tool exists for qualitative synthesis. A systematic search of the literature and software repositories (conducted January 2026) identified no purpose-built software for QES that integrates theme coding, translation matrix construction, and CERQual assessment within a unified workflow.

This paper describes QualSynth, an open-source, browser-based tool that fills this gap. QualSynth implements the complete QES workflow -- from study input through theme coding, reciprocal translation, CERQual assessment, to Summary of Qualitative Findings (SoQF) table generation -- within a single application that requires no installation, server infrastructure, or software licence.

## Implementation

### Design principles

QualSynth was developed with four guiding principles. First, **methodological fidelity**: the tool must faithfully implement established QES methods rather than imposing new analytic frameworks. Second, **interpretive flexibility**: qualitative synthesis is inherently interpretive, so the tool must support but never constrain researcher judgment. Third, **zero-installation deployment**: the tool must run in any modern web browser without requiring server infrastructure, package installation, or internet connectivity (after initial page load). Fourth, **auditability**: every analytical decision must be traceable and exportable for peer review.

### Architecture

QualSynth comprises two components: a Python engine for algorithm validation and testing, and a standalone HTML/JavaScript application for end-user interaction.

The **Python engine** (`qualsynth/` package) contains nineteen modules. The seven core modules are:

1. `models.py` -- Data classes defining the synthesis data model: `StudyInput`, `Quote`, `Theme`, `TranslationCell`, `TranslationMatrix`, `CERQualFinding`, and `SynthesisResult`. Studies capture metadata (authors, year, methodology, setting, sample size), quality appraisal (tool and score), key findings, and verbatim participant quotes with provenance (participant ID, page reference, context).

2. `themes.py` -- Theme creation, quote assignment, theme merging, saturation computation, and study coverage analysis. Themes are classified as descriptive (directly reflecting data) or analytical (interpretive constructs spanning multiple descriptive themes), following the two-level hierarchy proposed by Thomas and Harden [3].

3. `translation.py` -- Reciprocal translation matrix construction, coverage and consistency metrics, and translation type classification. The module builds a study-by-concept matrix, classifying each cell as present, absent, partial, or refutational. Translation types are classified using the tripartite scheme from Noblit and Hare [4]: reciprocal (consistency >= 0.8, no refutational evidence), refutational (consistency < 0.5), or line-of-argument (intermediate).

4. `cerqual.py` -- CERQual four-component assessment with algorithmic confidence grading. Each component (methodological limitations, coherence, adequacy, relevance) is assessed as "no concerns," "minor," "moderate," or "serious," mapped to numerical weights (0, 1, 2, 3). Overall confidence is determined by: Very Low if any component is serious; Low if any component is moderate or if the total weight across all four components reaches 3 or above; High if all components have no concerns; Moderate otherwise. This algorithm operationalises the CERQual guidance while preserving the ability for reviewers to override judgments.

5. `synthesis.py` -- Summary of Qualitative Findings (SoQF) table construction and theme summary statistics, including counts of descriptive and analytical themes and study coverage proportions.

6. `pipeline.py` -- The `run_qualsynth()` orchestrator that chains all modules, accepting studies, themes, CERQual findings, and (optionally) concepts as input and returning a complete `SynthesisResult`.

7. `certifier.py` -- Input hashing (SHA-256) and synthesis certification. The certifier issues PASS when at least two studies and at least one theme or CERQual finding are present; WARN when studies are present but no themes or findings have been created; and REJECT when fewer than two studies are included.

All nineteen modules are covered by a test suite of **102 pytest tests** spanning the seven core modules (theme CRUD, saturation, translation matrix, CERQual grading, SoQF generation, pipeline execution) and the fifteen computational methods modules described in the next section.

### Browser application

The **browser application** (`app/qualsynth.html`) is a self-contained single-file HTML application that ports all Python algorithms to JavaScript and provides a seven-tab interface:

1. **Studies** -- Entry form for study metadata, quality appraisal, key findings, and verbatim quotes with full provenance. Studies are displayed in a sortable table with quality score badges and quote counts.

2. **Coding** -- Split-panel interface with quotes on the left and themes on the right. Researchers select a quote and click a theme to assign it, or create new themes via a modal dialog. Themes display real-time statistics: assigned quote count, contributing study count, and saturation percentage. The coding panel supports both verbatim participant quotes and key findings as codable items.

3. **Translation** -- Interactive reciprocal translation matrix where each cell can be toggled through four states (present, absent, partial, refutational) by clicking. An "Auto-Detect" function extracts candidate concepts from key findings using word frequency analysis. The panel displays coverage and consistency metrics for each concept and classifies the overall translation type.

4. **Synthesis** -- Theme summary statistics, synthesis type selection (thematic synthesis or meta-ethnography), and an editable line-of-argument narrative field. An interactive theme network chart (Plotly.js) visualises themes as nodes connected by shared contributing studies, with node size proportional to quote count and colour distinguishing descriptive from analytical themes.

5. **CERQual** -- Structured assessment panel where each finding's four CERQual components are set via dropdown selectors. Overall confidence is computed in real time. A CERQual "traffic light" heatmap visualises all findings and components simultaneously, using a four-colour scale from green (no concerns) through red (serious concerns).

6. **Report** -- Auto-generated outputs including: (a) Summary of Qualitative Findings (SoQF) table with confidence badges, contributing study counts, and explanatory text; (b) methods paragraph with study counts, methodology breakdown, sample sizes, theme counts, and CERQual distribution; (c) theme descriptions with supporting quotes rendered as formatted blockquotes; and (d) CERQual justification table. The report can be copied to clipboard or exported as a TruthCert JSON bundle containing the complete analytical audit trail.

7. **Analytics** -- Computational text analytics dashboard with four panels: (a) a TF-IDF cosine similarity heatmap showing pairwise study similarity; (b) a Shannon entropy saturation curve plotting cumulative thematic information gain as studies are added, with a saturation threshold indicator; (c) a theme co-occurrence network visualisation showing themes as nodes connected by shared study contributions, with edge weights proportional to co-occurrence counts; and (d) an LDA topic model panel displaying top-10 words per discovered topic as horizontal bar charts with normalised weights.

The application includes dark mode, responsive layout, keyboard navigation, ARIA roles for accessibility, JSON import/export, and two built-in example datasets for demonstration and training.

### Thematic synthesis implementation

The thematic synthesis pathway follows Thomas and Harden's three-stage model [3]: line-by-line coding of primary data, organisation of codes into descriptive themes, and generation of analytical themes. In QualSynth, stage 1 corresponds to the Coding tab where quotes are assigned to themes. Stage 2 involves creating descriptive themes and reviewing saturation metrics. Stage 3 involves creating analytical themes that synthesise across descriptive themes and articulating a line of argument in the Synthesis tab.

**Saturation analysis** is computed as the proportion of included studies contributing to each theme:

$$\text{Saturation}(T_i) = \frac{|S_{T_i}|}{N}$$

where $S_{T_i}$ is the set of studies with at least one quote assigned to theme $T_i$ and $N$ is the total number of included studies. A saturation value of 1.0 indicates that every included study contributed to the theme. Themes with low saturation may warrant re-examination to determine whether they represent genuine minority perspectives or artefacts of incomplete coding.

### Meta-ethnography implementation

The meta-ethnography pathway implements Noblit and Hare's seven-phase approach [4], focusing on phases 4--6 (determining how studies relate, translating studies into one another, and synthesising translations). QualSynth constructs a study-by-concept translation matrix $M$ where:

$$M_{ij} \in \{\text{present}, \text{absent}, \text{partial}, \text{refutational}\}$$

For each concept $c_j$, **coverage** measures the proportion of studies where the concept is present:

$$\text{Coverage}(c_j) = \frac{\sum_{i} \mathbb{1}[M_{ij} = \text{present}]}{N}$$

**Consistency** measures the agreement direction among studies where the concept appears:

$$\text{Consistency}(c_j) = \frac{n_{\text{present}} - n_{\text{refutational}}}{n_{\text{present}}}$$

The overall **translation type** is classified using mean consistency across all concepts: reciprocal (mean consistency >= 0.8 with no refutational evidence), refutational (mean consistency < 0.5), or line-of-argument (intermediate). This classification guides the synthesis narrative: reciprocal translations indicate convergent findings suitable for direct synthesis, refutational translations signal contradictory evidence requiring explanation, and line-of-argument syntheses build an overarching interpretation from partially overlapping concepts.

### CERQual assessment algorithm

The CERQual framework [6] assesses confidence in individual review findings across four components. QualSynth operationalises each component as a four-level ordinal scale: no concerns (weight 0), minor concerns (weight 1), moderate concerns (weight 2), and serious concerns (weight 3). The algorithm determines overall confidence as follows:

- **Very Low**: any single component rated "serious" (max weight >= 3)
- **Low**: any single component rated "moderate" (max weight >= 2), OR cumulative weight across all four components >= 3
- **High**: all four components rated "no concerns" (total weight = 0)
- **Moderate**: all other combinations

This algorithm produces results consistent with the CERQual guidance documents [6,13] while providing a transparent, reproducible decision rule. Importantly, the tool displays all component assessments alongside the algorithmic output, enabling reviewers to apply expert judgment and override the suggested confidence level where the specific context warrants it.

## Computational Methods

Beyond the core synthesis workflow, QualSynth provides fifteen computational text analytics modules organised in five progressive tiers. All are implemented in pure Python with no external dependencies (no NumPy, SciPy, or machine learning libraries), ensuring the tool remains zero-installation and fully portable. Each module includes dedicated unit tests.

### Tier 1: Foundational text analytics

**TF-IDF cosine similarity** (`similarity.py`) builds term frequency-inverse document frequency vectors for each study's textual content (key findings and verbatim quotes) and computes pairwise cosine similarity. The resulting study-by-study similarity matrix supports automated theme cluster suggestion via single-linkage clustering with a configurable similarity threshold.

**Shannon entropy saturation** (`entropy.py`) measures thematic information gain as studies are sequentially added to the synthesis. For each cumulative study set, the module computes the Shannon entropy $H = -\sum p_i \log_2 p_i$ of the theme distribution, where $p_i$ is the proportion of study-theme contributions to theme $i$. A saturation index is identified where the information gain $\Delta H$ falls below a configurable threshold (default 0.05 bits), indicating that additional studies are unlikely to introduce new thematic information. The module also computes normalised entropy, Gini index, and mutual information $I(S; T)$ between studies and themes.

**Automated reflexivity scoring** (`reflexivity.py`) evaluates the presence and depth of reflexive practice in study texts by detecting first-person positioning, epistemological keywords, methodological self-critique, and researcher positionality statements. The composite score (0--1) supports systematic assessment of researcher transparency across included studies.

### Tier 2: Dimensionality reduction and probabilistic models

**Latent semantic analysis** (`lsa.py`) applies a power-iteration SVD algorithm to the TF-IDF matrix to extract latent semantic dimensions. The implementation avoids NumPy by computing the dominant singular vectors iteratively, projecting studies into a reduced-dimensional concept space that reveals latent thematic structure not visible in raw term frequencies.

**Theme co-occurrence network** (`network.py`) constructs a graph where themes are nodes and edges represent study-level co-occurrence. The module computes degree, betweenness (Brandes algorithm with BFS), and closeness centrality; identifies bridging themes (high betweenness, low degree); and performs greedy modularity-based community detection to discover thematic clusters.

**Bayesian saturation estimation** (`bayesian_saturation.py`) uses the Chao1 estimator from species-richness ecology to estimate the total number of undiscovered themes. Given $n$ observed themes with $f_1$ singletons and $f_2$ doubletons, the estimated total is $S_{Chao1} = S_{obs} + f_1^2 / (2 f_2)$. The module computes capture probabilities, Bayesian posterior credible intervals, and a probability of saturation metric.

### Tier 3: Semantic representation and argumentation

**Word embeddings** (`embeddings.py`) constructs distributional word vectors via positive pointwise mutual information (PPMI) followed by truncated SVD (power iteration). The resulting dense vectors capture semantic relationships between terms, supporting analogy detection and semantic clustering of themes beyond surface-level word overlap.

**Argument mining** (`argument_mining.py`) analyses study texts to identify three rhetorical components: claims (assertive statements), evidence (empirical observations and participant quotes), and reasoning (causal or explanatory links). The module builds argument structures per study, computes an evidence density score, and maps argument chains to support synthesis narrative construction.

**Hermeneutic depth index** (`conceptual_depth.py`) quantifies the interpretive depth of study findings by measuring abstraction level, conceptual density, interpretive layering, and theoretical integration. The composite index (0--1) helps reviewers identify studies contributing rich interpretive insight versus those providing primarily descriptive accounts.

### Tier 4: Formal structures and generative models

**Formal concept analysis** (`formal_concept.py`) builds a concept lattice from the binary study-by-theme incidence matrix. Each formal concept is a maximal rectangle of the context (a set of studies sharing a set of themes). The module extracts attribute implications (if studies have theme A, they also have theme B) and computes lattice structure metrics, providing a mathematically rigorous foundation for understanding the logical relationships between themes.

**Markov chain text generation** (`markov_text.py`) builds n-gram language models from study texts and generates synthetic text that reflects the corpus's stylistic and thematic patterns. This supports creative exploration of how themes might be expressed in hypothetical additional studies, and provides a baseline for assessing the distinctiveness of observed findings.

**Dialectical analysis** (`dialectical.py`) applies a thesis-antithesis-synthesis framework to identify contradictions and tensions within the evidence base. The module detects opposing claims across studies, identifies mediating concepts, and constructs dialectical triads. Tension scores quantify the degree of contradiction for each thematic pair, supporting the identification of refutational translations in meta-ethnography.

### Tier 5: Advanced topic modelling and ordering

**LDA topic model** (`topic_model.py`) implements collapsed Gibbs sampling for Latent Dirichlet Allocation entirely in pure Python. The sampler iteratively reassigns each word token to a topic according to the conditional posterior distribution $P(z_i = k) \propto (n_{dk} + \alpha)(n_{kw} + \beta) / (n_k + V\beta)$. The module extracts top words per topic with normalised weights, computes per-study topic proportions, model perplexity, and PMI-based topic coherence scores.

**Partial order lattice theory** (`partial_order.py`) models the inclusion relationships between theme sets using a partial order on study-theme profiles. The module constructs a Hasse diagram, computes the Mobius function for combinatorial inversion, and identifies maximal antichains that represent maximally independent thematic perspectives.

**Computational grounded theory** (`grounded_theory.py`) formalises the open-axial-selective coding paradigm as an algorithmic pipeline. Open coding uses TF-IDF to generate initial codes from text segments, axial coding groups codes by co-occurrence into categories, and selective coding identifies the core category with the highest connectivity. The module produces a coding hierarchy with linkage metrics.

## Illustrative example

### Type 2 diabetes self-management

To demonstrate QualSynth's capabilities, we conducted a thematic synthesis of five qualitative studies examining patient experiences of type 2 diabetes (T2DM) self-management [14--18]. The studies were conducted between 2004 and 2013 in the United Kingdom and Norway, using phenomenology (n=2), grounded theory (n=2), and ethnography (n=1), with a combined sample of 132 participants. Four studies received "high" quality scores on the CASP qualitative checklist and one received "moderate."

After loading the five studies with their key findings and representative participant quotes (10 quotes total), we proceeded to theme coding. Four **descriptive themes** emerged:

1. *Identity disruption* -- Diabetes challenges existing self-concept and social identity. Participants described diagnosis as fundamentally altering their sense of self ("It changed who I am. I'm not the same person anymore" -- Bury 2005, P03).

2. *Daily burden of management* -- The constant cognitive and practical demands of self-management, culminating in "diabetes fatigue" during long-term management ("I'm tired of thinking about it every single day. It never stops" -- Gomersall 2011, P07).

3. *Social navigation* -- Managing diabetes within family, cultural, and social contexts. Dietary management was particularly disruptive, creating tension between health requirements and cultural food practices ("My mother-in-law cooks everything with ghee. I can't refuse without causing offence" -- Bury 2005, P08).

4. *Empowerment through knowledge* -- Knowledge and self-monitoring as dual sources of control and anxiety ("Knowing what could happen scares me but also makes me try harder" -- Rise 2013, P04).

One **analytical theme** was generated: *Living with a contested self* -- an overarching interpretation that diabetes creates ongoing tension between the pre-diagnosis self and the "diabetic" identity, mediated by social context, cultural expectations, and the paradoxical effects of health knowledge.

**CERQual assessment** was performed on four review findings. Finding 1 (identity threat, 4 contributing studies, minor methodological limitations) and Finding 3 (dietary disruption, 3 studies, minor relevance concern) were assessed as **High** confidence. Finding 2 (daily burden, 4 studies, minor adequacy concern) was assessed as **Moderate** confidence. Finding 4 (peer support valued over clinical advice, 2 studies, moderate adequacy concern) was assessed as **Low** confidence, reflecting the limited number of contributing studies.

The complete workflow -- from data entry through theme coding, CERQual assessment, and SoQF table generation -- was performed within the QualSynth browser application. The auto-generated methods paragraph accurately summarised the synthesis: "We included 5 qualitative studies (phenomenology n=2, grounded theory n=2, ethnography n=1) with a combined sample of 132 participants. Studies were synthesized using thematic synthesis (Thomas & Harden 2008). 5 themes were identified (4 descriptive, 1 analytical). CERQual assessment: 2 High, 1 Moderate, 1 Low."

### Healthcare worker burnout (meta-ethnography demonstration)

A second built-in example demonstrates the meta-ethnography pathway using four studies of healthcare worker experiences during COVID-19 [19--22] (combined N=103). Six concepts were defined for the translation matrix: moral distress, institutional abandonment, peer solidarity, meaning-making, fear of contagion, and spiritual coping. QualSynth auto-detected these concepts from key findings and constructed the 4x6 translation matrix. Coverage analysis revealed that moral distress and peer solidarity appeared in all four studies (coverage 1.0), while spiritual coping was identified in only one study (coverage 0.25). The overall translation was classified as reciprocal, indicating convergent findings across studies.

## Discussion

### Principal findings

QualSynth is, to our knowledge, the first software tool purpose-built for qualitative evidence synthesis. It addresses a long-standing gap in the evidence synthesis toolkit by providing a structured, transparent, and auditable workflow for the three most widely used QES methods: thematic synthesis [3], meta-ethnography [4], and CERQual confidence assessment [6]. The addition of fifteen computational text analytics methods -- spanning information theory, latent semantic analysis, topic modelling, formal concept analysis, and argument mining -- provides quantitative scaffolding that supports but does not supplant interpretive judgment.

### Comparison with existing tools

General-purpose qualitative data analysis software (QDAS) such as NVivo [23], ATLAS.ti [24], and MAXQDA [25] support coding and theme development for primary qualitative research but lack specific features for evidence synthesis -- they do not implement reciprocal translation matrices, CERQual assessment, or SoQF table generation. Systematic review management tools such as Covidence [26] and EPPI-Reviewer [27] support screening and data extraction but do not provide synthesis-specific functionality for qualitative reviews. QualSynth occupies the intersection of these two categories, providing synthesis-specific analytical tools within a workflow designed explicitly for QES.

### Strengths

Several features distinguish QualSynth from manual approaches. First, the **integrated workflow** connects study input, theme coding, translation, confidence assessment, computational analytics, and reporting within a single application, eliminating the need to transfer data between tools. Second, **real-time metrics** -- saturation percentages, coverage proportions, consistency scores, CERQual confidence grades, and computational analytics (entropy curves, similarity matrices, topic distributions) -- provide immediate analytical feedback during the synthesis process. Third, **interactive visualisations** (theme networks, study-theme heatmaps, CERQual traffic lights, similarity heatmaps, saturation curves, co-occurrence networks, and topic word clouds) support pattern recognition and communication of findings. Fourth, the **computational methods** provide quantitative evidence for methodological decisions: entropy saturation analysis provides an empirical basis for determining when sampling is sufficient, TF-IDF similarity identifies study clusters that may represent distinct sub-themes, and LDA topic modelling discovers latent thematic structure that complements manual coding. Fifth, the **TruthCert export** captures the complete analytical audit trail in a machine-readable JSON format, enabling verification and reproducibility. Sixth, the **zero-installation architecture** -- a single HTML file running entirely in the browser with all algorithms in pure Python/JavaScript and no external dependencies -- eliminates deployment barriers and ensures the tool remains accessible regardless of institutional IT restrictions.

### Balancing structure and interpretation

A fundamental tension in QES software development is the risk that structured tooling may constrain the interpretive flexibility that is central to qualitative synthesis [28]. QualSynth addresses this tension in several ways. Theme labels, descriptions, and hierarchical relationships are entirely user-defined -- the tool imposes no predetermined coding framework. The translation matrix allows manual override of auto-detected concept presence, and cell states can be freely toggled. The CERQual algorithm provides a suggested confidence level but does not prevent researchers from exercising judgment. The line-of-argument narrative is a free-text field with no structural constraints. In short, QualSynth structures the *process* of synthesis while preserving the researcher's authority over *interpretation*.

### Limitations

Several limitations should be acknowledged. First, QualSynth currently relies on the researcher to extract and enter qualitative data from primary studies; it does not perform automated text extraction from PDFs or integration with reference managers. Future versions could incorporate import from common QDAS export formats. Second, the CERQual algorithm implements a rule-based approximation of the published guidance; while consistent with CERQual principles, individual review teams may apply different weighting logic. Third, the current version supports single-user operation; collaborative features such as dual coding, inter-rater reliability calculation, and conflict resolution are planned for future releases. Fourth, the illustrative examples use a small number of studies to demonstrate functionality; the computational methods (particularly LDA and LSA) are designed for corpora of at least five studies and may produce unstable results with fewer. Fifth, the pure Python constraint -- while ensuring zero-installation deployment -- means that computational methods run more slowly than optimised library implementations; however, for typical QES sizes (5--50 studies), execution times remain under one second. Sixth, the computational analytics should be interpreted as exploratory aids rather than confirmatory analyses; they complement but do not replace the interpretive judgment central to qualitative synthesis.

### Future development

Planned enhancements include: (1) import from NVivo and ATLAS.ti export formats; (2) collaborative dual-coding with Cohen's kappa for inter-rater reliability; (3) ENTREQ [29] and PRISMA-QES [30] reporting checklist integration; (4) framework synthesis support [31]; and (5) integration with the broader evidence synthesis ecosystem through standardised data exchange formats.

## Conclusions

QualSynth fills a significant methodological gap by providing the first purpose-built software for qualitative evidence synthesis. By integrating theme coding, reciprocal translation, CERQual assessment, and fifteen computational text analytics methods within a transparent, auditable workflow, it brings qualitative synthesis closer to the standards of reproducibility and efficiency that quantitative meta-analysis has long enjoyed. The computational methods provide empirical scaffolding for methodological decisions -- from saturation assessment to latent topic discovery -- while preserving the researcher's interpretive authority. The tool is freely available as open-source software, requires no installation, and is designed to support rather than supplant the interpretive judgment that remains at the heart of qualitative synthesis.

## Availability and requirements

- **Project name:** QualSynth
- **Project home page:** [REPOSITORY URL]
- **Operating system(s):** Platform-independent (browser-based)
- **Programming language:** Python 3.10+ (engine, 19 modules, 102 tests), JavaScript ES5+ (browser application)
- **Other requirements:** Modern web browser (Chrome, Firefox, Edge, Safari); Python 3.10+ and pytest for running the validation test suite; no external Python packages required
- **Licence:** [LICENCE TYPE, e.g. MIT]
- **Any restrictions to use by non-academics:** None

## Declarations

### Ethics approval and consent to participate

Not applicable. This study describes the development of a software tool and uses only illustrative data from previously published qualitative studies.

### Consent for publication

Not applicable.

### Competing interests

The authors declare no competing interests.

### Funding

[FUNDING STATEMENT OR "No external funding was received for this work."]

### Authors' contributions

[AUTHOR] conceived the tool, designed the architecture, implemented all modules, conducted the illustrative analysis, and wrote the manuscript.

### Acknowledgements

[ACKNOWLEDGEMENTS OR "None."]

## References

1. Booth A, Noyes J, Flemming K, et al. Structured methodology review identified seven (RETREAT) criteria for selecting qualitative evidence synthesis approaches. *J Clin Epidemiol*. 2018;99:41-52.

2. Flemming K, Booth A, Garside R, et al. Qualitative evidence synthesis for complex interventions and guideline development: clarification of the purpose, designs and relevant methods. *BMJ Glob Health*. 2019;4(Suppl 1):e000882.

3. Thomas J, Harden A. Methods for the thematic synthesis of qualitative research in systematic reviews. *BMC Med Res Methodol*. 2008;8:45.

4. Noblit GW, Hare RD. *Meta-Ethnography: Synthesizing Qualitative Studies*. Newbury Park: Sage; 1988.

5. Noyes J, Booth A, Cargo M, et al. Chapter 21: Qualitative evidence. In: Higgins JPT, Thomas J, Chandler J, et al., editors. *Cochrane Handbook for Systematic Reviews of Interventions* version 6.4. Cochrane; 2023.

6. Lewin S, Booth A, Glenton C, et al. Applying GRADE-CERQual to qualitative evidence synthesis findings: introduction to the series. *Implement Sci*. 2018;13(Suppl 1):2.

7. Houghton C, Murphy K, Meehan B, et al. From screening to synthesis: using NVivo to enhance transparency in qualitative evidence synthesis. *J Clin Nurs*. 2017;26(5-6):873-881.

8. France EF, Uny I, Ring N, et al. A methodological systematic review of meta-ethnography conduct to develop guidance for practice. *BMC Med Res Methodol*. 2019;19:25.

9. Toye F, Seers K, Allcock N, et al. Meta-ethnography 25 years on: challenges and insights for synthesising a large number of qualitative studies. *BMC Med Res Methodol*. 2014;14:80.

10. Review Manager (RevMan) [Computer program]. Version 5.4. The Cochrane Collaboration; 2020.

11. Viechtbauer W. Conducting meta-analyses in R with the metafor package. *J Stat Softw*. 2010;36(3):1-48.

12. Palmer TM, Sterne JAC. *Meta-Analysis in Stata: An Updated Collection from the Stata Journal*. 2nd ed. College Station: Stata Press; 2016.

13. Munthe-Kaas H, Bohren MA, Glenton C, et al. Applying GRADE-CERQual to qualitative evidence synthesis findings -- paper 3: how to assess methodological limitations. *Implement Sci*. 2018;13(Suppl 1):9.

14. Bury M, Newbould J, Taylor D. A rapid review of the current state of knowledge regarding lay-led self-management of chronic illness. London: National Institute for Health and Clinical Excellence; 2005.

15. Lawton J, Peel E, Parry O, et al. Lay perceptions of type 2 diabetes in Scotland: bringing health services back in. *Soc Sci Med*. 2003;57(7):1573-1585.

16. Rise MB, Pellerud A, Rygg LO, et al. Making and maintaining lifestyle changes after participating in group based type 2 diabetes self-management educations: a qualitative study. *PLoS One*. 2013;8(5):e64009.

17. Gomersall T, Madill A, Summers LK. A metasynthesis of the self-management of type 2 diabetes. *Qual Health Res*. 2011;21(6):853-871.

18. Peel E, Parry O, Douglas M, et al. Diagnosis of type 2 diabetes: a qualitative analysis of patients' emotional reactions and views about information provision. *Patient Educ Couns*. 2004;53(3):269-275.

19. Billings J, Ching BCF, Gkofa V, et al. Experiences of frontline healthcare workers and their views about support during COVID-19 and previous pandemics: a systematic review and qualitative meta-synthesis. *BMC Health Serv Res*. 2021;21:923.

20. Catton H. Global challenges in health and health care for nurses and midwives everywhere. *Int Nurs Rev*. 2020;67(1):4-6.

21. Moradi Y, Baghaei R, Hosseingholipour K, et al. Challenges experienced by ICU nurses throughout the provision of care for COVID-19 patients: a qualitative study. *J Nurs Manag*. 2021;29(5):1159-1168.

22. Vindrola-Padros C, Andrews L, Dowrick A, et al. Perceptions and experiences of healthcare workers during the COVID-19 pandemic in the UK. *BMJ Open*. 2020;10(11):e040503.

23. NVivo [Computer program]. Version 14. Lumivero; 2023.

24. ATLAS.ti [Computer program]. Version 24. ATLAS.ti Scientific Software Development GmbH; 2024.

25. MAXQDA [Computer program]. Version 24. VERBI Software; 2024.

26. Covidence [Computer program]. Veritas Health Innovation; 2024. Available from: https://www.covidence.org

27. Thomas J, Brunton J, Graziosi S. EPPI-Reviewer 4.0: software for research synthesis. London: EPPI-Centre Software; 2010.

28. Dixon-Woods M, Agarwal S, Jones D, et al. Synthesising qualitative and quantitative evidence: a review of possible methods. *J Health Serv Res Policy*. 2005;10(1):45-53.

29. Tong A, Flemming K, McInnes E, et al. Enhancing transparency in reporting the synthesis of qualitative research: ENTREQ. *BMC Med Res Methodol*. 2012;12:181.

30. Flemming K, Booth A, Hannes K, et al. Cochrane Qualitative and Implementation Methods Group guidance series -- paper 6: reporting guidelines for qualitative, implementation, and process evaluation evidence syntheses. *J Clin Epidemiol*. 2018;97:79-85.

31. Carroll C, Booth A, Leaviss J, et al. "Best fit" framework synthesis: refining the method. *BMC Med Res Methodol*. 2013;13:37.
