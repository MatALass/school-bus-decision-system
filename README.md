# Electric School Bus Decision System

A portfolio-grade Streamlit project by **Mathieu Alassoeur** that transforms a large public Excel workbook on electric school bus adoption in the United States into a **decision-support product**.

This is not positioned as a generic dashboard. The project is built around three decision questions:

1. **Where is electric school bus adoption already material?**
2. **Where does deployment still appear misaligned with environmental and socioeconomic need?**
3. **Which districts should be prioritized first under explicit, reviewable scoring assumptions?**

## What makes this version strong

The final package is intentionally narrower and stronger than a broad exploratory dashboard.

It keeps only the pages that carry real analytical value:

- **Executive briefing** for a recruiter or stakeholder entry point
- **Strategy and inequity** to isolate adoption-vs-need misalignment
- **Decision engine** to move from description to prioritization
- **District deep dive** for local benchmarking and district-level interpretation
- **Market and ecosystem** to surface OEM, utilities, funding, and rollout constraints
- **Methodology and caveats** to make assumptions and limits explicit

It also adds scenario-based scoring profiles so the ranking can move with the decision lens rather than pretending one frozen weighting is universally correct.

## Core analytical logic

### Priority score
The priority score combines four transparent blocks:

- **Need**: PM2.5, low-income share, free/reduced lunch, poverty, disability
- **Transition gap**: low ESB adoption, low operating conversion, fragmented funding
- **Scale**: fleet size
- **Complexity**: utility fragmentation, county span, congressional span

### Quick-win score
A second score highlights districts where action may be easier to execute because the workbook already suggests stronger rollout traction or lower coordination burden.

### Decision segments
Districts are grouped into four action buckets:

- **Act now**
- **High need, harder execution**
- **Fast-track candidate**
- **Monitor**

### Scenario profiles
The decision engine includes multiple profiles:

- **Balanced**
- **Equity first**
- **Deployment first**
- **Scale first**

That makes the system more defensible: users can see how prioritization changes when policy intent changes.

## Project structure

```text
.
├── app.py
├── data/
│   ├── data.xlsx
│   └── processed/
├── pages/
│   ├── decision_engine.py
│   ├── district_explorer.py
│   ├── equity.py
│   ├── executive.py
│   ├── fleet_tech.py
│   └── methodology.py
├── scripts/
│   └── export_priority_snapshot.py
├── src/
│   ├── components/
│   ├── data/
│   ├── school_bus_cli/
│   └── utils/
├── .streamlit/
├── pyproject.toml
└── README.md
```

## Installation

```bash
pip install -e .
```

## Run locally

```bash
streamlit run app.py
```

## Export decision outputs

```bash
school-bus-export-priority
```

This generates:

- `data/processed/district_priority_snapshot.csv`
- `data/processed/state_priority_snapshot.csv`

The Decision Engine page also lets you download a shortlist CSV directly from the UI.


## Engineering quality

This repository now includes an expanded automated test suite for preprocessing, scoring helpers, ranking behavior, and rollup consistency, plus a GitHub Actions CI workflow that runs the tests on every push and pull request. The raw workbook remains committed intentionally because it is the canonical public input used to reproduce the decision engine locally.

## Why this project is portfolio-grade

Many student dashboards stop at visual description. This one goes further by:

- narrowing the story to a **small number of strong insights**
- separating **scale**, **equity alignment**, **market structure**, and **execution burden** instead of collapsing them into one vague narrative
- exposing the prioritization logic instead of hiding it behind a black-box score
- allowing the ranking to change under different scenario profiles
- producing exportable artifacts that support downstream briefing or triage
- documenting methodological caveats clearly instead of overclaiming certainty

## Honest limitations

- the score is **relative to the workbook**, not a full operational truth
- several inputs still contain meaningful missingness
- implementation readiness is inferred through proxies, not measured directly
- this is a **decision-oriented descriptive system**, not a predictive deployment model

Those limits are intentional and preferable to a more ambitious but less defensible pseudo-ML framing.

## Recommended presentation angle

For portfolio or interview use, present the project as:

**“a decision-support analytics product built from messy public workbook data, not just a dashboard.”**

That framing is more accurate and stronger than presenting it as pure BI or generic data visualization.
