"""Site-wide Open Graph social-card PNG (EDIT-02 + UI-SPEC OG:image Spec).

Produces a 1200x630 PNG of the scissors chart (strike vs market price over
time) for use as the site's <meta property="og:image"> social preview.

Usage:
    from pipeline.build_og_image import build
    build("src/data/chart-3c.json", "src/assets/og-card.png")
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OKABE_BLUE = "#0072B2"
OKABE_ORANGE = "#E69F00"


def build(chart_json_path: Path | str, out_path: Path | str) -> Path:
    """Render a 1200x630 OG-card PNG from the chart-3c view-model JSON.

    Args:
        chart_json_path: Path to src/data/chart-3c.json (or any chart-3c artefact).
        out_path: Destination PNG path (parent directories created if absent).

    Returns:
        Path of the written PNG file.
    """
    rows = json.loads(Path(chart_json_path).read_text())

    # Aggregate across allocation rounds to a single "All" series for the card
    by_month: dict[str, dict[str, float]] = {}
    for r in rows:
        m = r["month"]
        agg = by_month.setdefault(m, {"sw": 0.0, "mw": 0.0, "g": 0.0})
        agg["sw"] += r["strike"] * r["generation_mwh"]
        agg["mw"] += r["market"] * r["generation_mwh"]
        agg["g"] += r["generation_mwh"]

    months = sorted(by_month)
    strike = [by_month[m]["sw"] / by_month[m]["g"] for m in months]
    market = [by_month[m]["mw"] / by_month[m]["g"] for m in months]

    # figsize (12, 6.3) at dpi=100 -> 1200x630 pixels
    fig, ax = plt.subplots(figsize=(12, 6.3), dpi=100)

    ax.plot(months, strike, color=OKABE_BLUE, linewidth=2.5, label="Strike price")
    ax.plot(months, market, color=OKABE_ORANGE, linewidth=2.5,
            label="Market reference price")

    ax.set_ylabel("£ / MWh", fontsize=14)
    ax.set_title("CfD Visualiser", loc="left", fontsize=22, fontweight="semibold")
    ax.set_title(
        "Consumers paid the gap in every year except 2022.",
        loc="right",
        fontsize=12,
    )
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=12)

    # Show every 12th month label for readability (avoid overlapping ticks)
    tick_idx = list(range(0, len(months), 12))
    ax.set_xticks(tick_idx)
    ax.set_xticklabels([months[i] for i in tick_idx], rotation=0)

    fig.tight_layout()

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=100, format="png")
    plt.close(fig)
    return out
