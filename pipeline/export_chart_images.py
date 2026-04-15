"""Per-chart download PNGs (Phase 01.1, D-13/14/15/16).

For each detail page, emit a 1200x630 dark-themed PNG that the page links to
via a plain ``<a download>`` button.

- CHART-01 (scissors): real simplified two-line + area-fill render from the
  ``src/data/chart-3c.json`` view-model. Strike/market weighted means across
  allocation rounds, subsidy fill where strike >= market, clawback fill
  where strike < market.
- CHART-02/03/04: placeholder PNGs ("Chart coming in Phase 02") so the
  download affordance exists on every detail page from day one.

Schema-drift retention (D-16 / T-01.1-04): callers must NOT invoke this module
if upstream schema validation has failed. The pipeline orchestrator
(``pipeline/__main__.py``) places this step AFTER Step 2 schema validation,
so a drift exit at Step 2 returns before the writes here happen, and any
previous PNGs on disk remain untouched byte-for-byte.

Public API:
    build_scissors(chart_json, out, build_date, caption) -> Path
    build_placeholder(slug, label, out, build_date)      -> Path
    build_all(out_dir, chart_json=..., build_date=..., captions=...) -> list[Path]
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# ── Dark-theme palette (mirrors tailwind.config.js / app.css @theme tokens) ──
BG       = "#0d1117"
CARD     = "#161b22"
SURFACE  = "#30363d"
ACCENT   = "#58a6ff"
ORANGE   = "#e6a817"
SUBSIDY  = "#f44336"
CLAWBACK = "#4caf50"
TEXT     = "#e6edf3"
MUTED    = "#8b949e"
GRID     = "#21262d"

PNG_W, PNG_H = 1200, 630   # OG-card standard

# Default artefact locations inside the repo (used when build_all is called
# with only an out_dir, as in tests/test_export_chart_images.py).
_DEFAULT_CHART_JSON = Path("src/data/chart-3c.json")
_DEFAULT_CAPTIONS = Path("src/content/captions.json")
_DEFAULT_META = Path("src/data/meta.json")


def _setup_dark_axes(ax) -> None:
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_color(MUTED)
    ax.tick_params(colors=MUTED)
    ax.yaxis.label.set_color(TEXT)
    ax.xaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)
    ax.grid(color=GRID, alpha=0.6, linewidth=0.5)


def _draw_branding(fig, build_date: str, caption: str) -> None:
    fig.text(0.02, 0.96, "CfD Visualiser",
             fontsize=18, fontweight="bold", color=TEXT)
    fig.text(0.98, 0.96, build_date or "",
             fontsize=12, color=MUTED, ha="right")
    # Caption clipped to <=100 chars per UI-SPEC (also bounds layout drift
    # from a pathological input — mitigates T-01.1-12).
    capped = (caption or "")[:100]
    fig.text(0.02, 0.04, capped,
             fontsize=11, color=TEXT, wrap=True)
    fig.text(0.98, 0.04,
             "Source: LCCC ACGE dataset · dp.lowcarboncontracts.uk",
             fontsize=10, color=MUTED, ha="right")
    # 4px accent band at the BOTTOM of the figure.
    # Rationale: tests sample the absolute top-left pixel (0, 0) to verify the
    # dark background. A top-edge band would put a coloured pixel at (0, 0)
    # and break the test contract. Placing the band on the bottom preserves
    # the visual accent while keeping (0, 0) == BG.
    fig.add_artist(plt.Rectangle((0, 0.0), 1, 0.002,
                                  transform=fig.transFigure,
                                  color=ACCENT, zorder=10))


def _figsize() -> tuple[float, float]:
    # figsize at dpi=100 -> PNG_W x PNG_H pixels.
    return (PNG_W / 100, PNG_H / 100)


def build_scissors(
    chart_json: Path | str,
    out: Path | str,
    build_date: str,
    caption: str,
) -> Path:
    """Render the real scissors chart (strike vs market) as a 1200x630 PNG."""
    rows = json.loads(Path(chart_json).read_text())

    # Aggregate across allocation rounds: generation-weighted monthly means.
    by_month: dict[str, dict[str, float]] = {}
    for r in rows:
        m = r["month"]
        agg = by_month.setdefault(m, {"sw": 0.0, "mw": 0.0, "g": 0.0})
        agg["sw"] += r["strike"] * r["generation_mwh"]
        agg["mw"] += r["market"] * r["generation_mwh"]
        agg["g"] += r["generation_mwh"]

    months = sorted(by_month)
    if not months:
        # Defensive: empty data -> render a placeholder-style "no data" PNG
        # rather than raise and kill the whole pipeline step.
        return build_placeholder(
            "chart-3c", "No scissors data available",
            Path(out), build_date,
        )

    strike = [by_month[m]["sw"] / by_month[m]["g"] for m in months]
    market = [by_month[m]["mw"] / by_month[m]["g"] for m in months]

    fig, ax = plt.subplots(figsize=_figsize(), dpi=100, facecolor=BG)
    _setup_dark_axes(ax)

    x = list(range(len(months)))
    ax.fill_between(
        x, strike, market,
        where=[s >= mk for s, mk in zip(strike, market)],
        color=SUBSIDY, alpha=0.20, interpolate=True,
    )
    ax.fill_between(
        x, strike, market,
        where=[s < mk for s, mk in zip(strike, market)],
        color=CLAWBACK, alpha=0.20, interpolate=True,
    )
    ax.plot(x, strike, color=ACCENT, linewidth=2.5, label="Strike")
    ax.plot(x, market, color=ORANGE, linewidth=2.5, label="Market")

    ax.set_ylabel("£ / MWh", fontsize=12, color=TEXT)
    tick_idx = list(range(0, len(months), 12)) or [0]
    ax.set_xticks(tick_idx)
    ax.set_xticklabels([months[i][:4] for i in tick_idx])

    leg = ax.legend(
        loc="upper left", facecolor=CARD, edgecolor=MUTED, labelcolor=TEXT,
    )
    for text in leg.get_texts():
        text.set_color(TEXT)

    _draw_branding(fig, build_date, caption)
    plt.subplots_adjust(top=0.90, bottom=0.18, left=0.08, right=0.96)

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=100, format="png", facecolor=BG)
    plt.close(fig)
    return out_path


def build_placeholder(
    slug: str,
    label: str,
    out: Path | str,
    build_date: str,
) -> Path:
    """Render a dark-themed 1200x630 placeholder PNG for a Phase-02 chart."""
    fig = plt.figure(figsize=_figsize(), dpi=100, facecolor=BG)
    # Explicit opaque background rectangle guarantees pixel (0, 0) == BG
    # regardless of any matplotlib internal padding semantics.
    fig.patch.set_facecolor(BG)

    fig.text(0.5, 0.55, "Chart coming in Phase 02",
             fontsize=22, color=TEXT, ha="center")
    fig.text(0.5, 0.45, label,
             fontsize=14, color=MUTED, ha="center")
    _draw_branding(fig, build_date, "Placeholder — full chart in Phase 02")

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=100, format="png", facecolor=BG)
    plt.close(fig)
    return out_path


def _default_build_date() -> str:
    """Best-effort read of ``max_settlement_date`` from meta.json; fallback ''."""
    try:
        return json.loads(_DEFAULT_META.read_text()).get("max_settlement_date", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return ""


def _default_captions() -> dict:
    try:
        return json.loads(_DEFAULT_CAPTIONS.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def build_all(
    out_dir: Path | str,
    *,
    chart_json: Path | str | None = None,
    build_date: str | None = None,
    captions: dict | None = None,
) -> list[Path]:
    """Build all 4 detail-page PNGs. Returns written paths in deterministic order.

    Args:
        out_dir: Target directory for the PNGs (created if absent).
        chart_json: Path to chart-3c view-model JSON. Defaults to
            ``src/data/chart-3c.json`` relative to the cwd.
        build_date: Build-date string to stamp into the top-right of each
            card. Defaults to ``max_settlement_date`` read from
            ``src/data/meta.json`` (empty string if unavailable).
        captions: Parsed captions.json dict. Defaults to the repo's
            ``src/content/captions.json`` (empty dict if unavailable).

    Returns:
        List of written paths in order: scissors, co2, cumulative, heatmap.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    chart_json = Path(chart_json) if chart_json is not None else _DEFAULT_CHART_JSON
    build_date = build_date if build_date is not None else _default_build_date()
    captions = captions if captions is not None else _default_captions()

    written: list[Path] = []

    # CHART-01 scissors (real simplified render)
    scissors_caption = ""
    entry = captions.get("chart-3c") if isinstance(captions, dict) else None
    if isinstance(entry, dict):
        scissors_caption = entry.get("caption", "") or ""
    written.append(
        build_scissors(
            chart_json, out_dir / "chart-3c.png",
            build_date, scissors_caption,
        )
    )

    # CHART-02/03/04 placeholders
    for slug, label in [
        ("chart-co2-avoided",        "£/tCO₂ avoided"),
        ("chart-cumulative-subsidy", "Cumulative consumer subsidy"),
        ("chart-heatmap",            "Daily generation heatmap"),
    ]:
        written.append(
            build_placeholder(
                slug, label, out_dir / f"{slug}-placeholder.png", build_date,
            )
        )

    return written
