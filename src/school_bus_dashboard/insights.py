from __future__ import annotations

import pandas as pd

from school_bus_dashboard.metrics import comparison_label


def build_summary_lines(scope_name: str, scope_metrics: dict[str, float], benchmark_metrics: dict[str, float]) -> list[str]:
    adoption_label = comparison_label(
        scope_metrics["adoption_rate"],
        benchmark_metrics["adoption_rate"],
        reverse=False,
    )
    pollution_label = comparison_label(
        scope_metrics["avg_pm25"],
        benchmark_metrics["avg_pm25"],
        reverse=True,
    )
    income_label = comparison_label(
        scope_metrics["avg_income"],
        benchmark_metrics["avg_income"],
        reverse=False,
    )
    vulnerability_label = comparison_label(
        scope_metrics["avg_free_lunch_pct"],
        benchmark_metrics["avg_free_lunch_pct"],
        reverse=True,
    )

    return [
        f"**ESB adoption**: {scope_metrics['adoption_rate']:.1f}% — {adoption_label}.",
        f"**Air quality exposure (PM2.5)**: {scope_metrics['avg_pm25']:.2f} — {pollution_label}.",
        f"**Median household income**: ${scope_metrics['avg_income']:,.0f} — {income_label}.",
        f"**Student economic vulnerability**: {scope_metrics['avg_free_lunch_pct']:.1f}% — {vulnerability_label}.",
        f"**Interpretation**: {scope_name} should be prioritized when pollution and vulnerability remain high while ESB adoption is still lagging.",
    ]


def build_methodology_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["PM2.5 concentration", "35%", "Higher pollution = stronger electrification need"],
            ["Free/reduced lunch share", "30%", "Higher vulnerability = stronger equity need"],
            ["ESB adoption gap", "20%", "Lower adoption = more room for intervention"],
            ["Income need score", "15%", "Lower household income = lower local capacity"],
        ],
        columns=["Component", "Weight", "Rationale"],
    )
