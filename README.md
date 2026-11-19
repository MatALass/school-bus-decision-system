# Electric School Bus Decision System

A Streamlit application that turns the public WRI workbook on electric school bus (ESB) adoption in the United States into a prioritisation tool for school districts.

It answers three questions:

1. Where is ESB adoption already significant?
2. Where does deployment not match environmental and socioeconomic need?
3. Which districts should come first, under weights that can be read and changed?

## Data

`data/raw/data.xlsx` is the WRI *Dataset of Electric School Bus Adoption in the United States*. The app reads six of its sheets: districts, buses, states, utilities, counties and congressional districts. The workbook is committed so that the results can be reproduced as they are.

## Method

### Priority score

Each district gets a score from 0 to 100 built from four min-max normalised blocks:

| Block | Inputs | Default weight |
| --- | --- | --- |
| Need | PM2.5, low-income share, free or reduced price lunch, poverty, disability | 0.45 |
| Transition gap | low ESB adoption, low share of buses in operation, fragmented funding | 0.35 |
| Scale | fleet size (log) | 0.10 |
| Complexity | number of utilities, counties and congressional districts covered | 0.10 |

Four weighting profiles show how the ranking moves with the policy goal:

| Profile | Need | Transition gap | Scale | Complexity |
| --- | --- | --- | --- | --- |
| Balanced | 0.45 | 0.35 | 0.10 | 0.10 |
| Equity first | 0.60 | 0.25 | 0.05 | 0.10 |
| Deployment first | 0.35 | 0.40 | 0.15 | 0.10 |
| Scale first | 0.30 | 0.30 | 0.30 | 0.10 |

### Quick-win score

A second score flags districts where action looks easier to start: need, scale, adoption gap and signs of rollout readiness in the workbook.

### Decision segments

| Segment | Rule |
| --- | --- |
| Act now | top quartile on both scores |
| High need, harder execution | top quartile on priority only |
| Fast-track candidate | top quartile on quick win only |
| Monitor | everything else |

## Pages

- **Executive briefing**: headline figures and the main findings.
- **Strategy and inequity**: adoption compared with need.
- **Decision engine**: ranking, profiles, segments, and a CSV download of the shortlist.
- **District deep dive**: one district against its state and peers.
- **Market and ecosystem**: manufacturers, utilities and funding sources.
- **Methodology and caveats**: definitions and limits.

## Run it

Python 3.11 or later.

```bash
pip install -e .
streamlit run app.py
```

Export the district and state rankings to `data/processed/`:

```bash
school-bus-export-priority
```

Tests (preprocessing, scoring, ranking and state roll-ups) run in GitHub Actions on every push and pull request:

```bash
pytest -q
```

## Project structure

```text
app.py                  Streamlit entry point
pages/                  one module per page
src/data/               loading, preprocessing, scoring and segments
src/components/         charts and UI helpers
src/school_bus_cli/     export command
scripts/                export script
tests/                  unit tests
data/raw/               source workbook
```

## Limits

- Scores are relative to the districts in the workbook, not absolute measures.
- Several inputs have many missing values.
- Readiness is inferred from proxies, not measured.
- The tool ranks and describes; it does not predict future deployment.

## License

MIT
