# CfD Data Visualisation Suite — Project Scope

A catalogue of visualisations to build from the LCCC *Actual CfD Generation and Avoided GHG Emissions* dataset (and, where noted, a small number of external joins). Each visualisation is framed around the specific weakness or defect in the UK renewables subsidy regime it is intended to expose.

Ordered roughly by informational payload.

---

## 1. Capacity factor and its decay

### 1a. Monthly capacity factor by technology (time series)
For each CfD unit, compute
`CF = generation_MWh / (capacity_MW × hours_in_month)`.
Plot CF by month for offshore wind, onshore wind, solar, biomass.

- **External data required:** installed capacity (MW) per CfD unit, from the LCCC *CfD Register* on the same data portal.
- **Reveals:** seasonality (solar ~2 % in December, ~18 % in June) and tests the "offshore wind runs at ~50 %" claim.

### 1b. Capacity-factor degradation curve
For each offshore wind farm, plot CF vs. years-since-commissioning, with fitted slope.

- **Reveals:** industry assumes ~0 % degradation; academic estimates (Staffell & Green) are ~1.6 %/yr. A visible negative slope undermines LCOE assumptions.

### 1c. Fleet-wide CF distribution (violin/box plot per year)
Distribution across all assets, per year.

- **Reveals:** the headline average conceals wide variance — some farms deliver 25 %, others 55 %.

---

## 2. Intermittency and dark-doldrums exposure

### 2a. Daily generation heatmap (year × day-of-year)
Total wind + solar CfD MWh as a colour grid.

- **Reveals:** *dunkelflaute* weeks (cold, still, dark — typically late November / early February) appear as vertical low-output stripes. Visually arresting.
- **Data:** CSV only.

### 2b. Load-duration curve
Sort daily generation descending, plot on log x-axis, overlay a flat gas baseload reference.

- **Reveals:** fleet delivers >80 % of peak for only a small fraction of hours.

### 2c. Rolling 7-day minimum generation
Worst-week-of-the-year time series.

- **Reveals:** scale of storage/backup that would be needed to cover the observed worst case.

---

## 3. Subsidy economics

### 3a. £/MWh subsidy time series, by allocation round
Separate lines for Investment Contracts, AR1, AR2, AR4, AR5.

- **Reveals:** Investment Contracts are the cost millstone; newer rounds are (in theory) cheap, but barely generating yet.

### 3b. Cumulative consumer subsidy (£bn), stacked by technology
Area chart climbing toward the current ~£13 bn total.

- **Reveals:** offshore wind and Hinkley Point C dominate the cost.

### 3c. Strike-price vs. wholesale-price "scissors" chart
Two lines; gap = subsidy per MWh.

- **Reveals:** lines cross briefly in 2022, then reopen. Counters the "CfDs save consumers money" narrative.

### 3d. Subsidy-per-tonne-CO₂-avoided
`CFD_Payments_GBP / Avoided_GHG_tonnes_CO2e` by year and by technology, overlaid with UK ETS price (~£35–80/t) and DEFRA social cost of carbon (~£280/t).

- **Reveals:** many years land at £200–400/tCO₂ — more expensive than the government's own carbon value. Among the most damning single charts in the suite.

### 3e. Bang-for-buck scatter
Per project: x = total subsidy £m, y = total tCO₂ avoided. Diagonal reference line.

- **Reveals:** Hinkley and Investment Contract offshore wind farms sit well below the line (expensive abatement).

---

## 4. The cannibalisation effect

### 4a. Wholesale capture price vs. fleet wind output
Scatter of daily (or half-hourly via Elexon) wholesale price against total UK wind generation.

- **Reveals:** strong negative correlation. High wind → collapsed prices → bigger subsidy top-ups. The mechanical reason why more wind makes each new MW less economic.
- **External data:** Elexon / NESO wholesale prices.

### 4b. Capture-price ratio by year
(Volume-weighted price wind actually received) ÷ (time-weighted average wholesale price).

- **Reveals:** falls from ~100 % toward 70–80 % as penetration rises.

---

## 5. Curtailment and grid constraints

### 5a. Estimated curtailment vs. generation
Pair LCCC delivered-MWh with NESO Balancing Mechanism data to show £m/year paid to (mostly Scottish) wind farms *to switch off* because the grid cannot move the power south.

- **External data:** NESO BMRS (`bmrs-api.elexonportal.co.uk`).
- **Reveals:** constraint payments to Viking, Seagreen and similar assets — a cost borne by consumers outside the CfD envelope.

---

## 6. Concentration and lock-in

### 6a. Lorenz curve of subsidy receipts by project
X = cumulative % of projects, Y = cumulative % of £ received.

- **Reveals:** typically ~80 % of subsidy accrues to ~10 projects. The "renewables story" is really Hinkley plus a handful of early offshore wind farms.

### 6b. Remaining contract-years outstanding
Stacked bar of £bn of *future* subsidy obligations by contract expiry year. CfDs run 15 years, Hinkley 35.

- **Reveals:** consumers are locked into Investment Contract costs into the late 2030s regardless of how cheap later rounds clear.

---

## 7. The 2022 clawback in context

### 7a. Monthly net payment chart
Show monthly net CfD settlement alongside cumulative subsidy.

- **Reveals:** the headline 2022 refund (~£345 m) is a small dent in an otherwise rising curve. Antidote to "CfDs saved consumers money" framing.

---

## Recommended delivery order

A sensible build order balancing informational payload against external data dependencies:

**Phase 1 — CSV only, maximum impact:**
1. **3c** Strike vs market scissors chart
2. **3d** £/tCO₂ avoided by round and year
3. **3b + 6a** Cumulative subsidy stacked by project, with Lorenz curve
4. **2a** Daily generation heatmap

**Phase 2 — unlock capacity-factor family:**
5. Join CfD Register (capacity per unit)
6. **1a, 1b, 1c** Capacity factor, degradation, distribution

**Phase 3 — external joins:**
7. **4a, 4b** Cannibalisation (Elexon wholesale prices)
8. **5a** Curtailment and constraint payments (NESO BMRS)
9. **6b** Lock-in tail
10. **7a** 2022 clawback in context

---

## Data inputs summary

| Source | Used by |
|---|---|
| LCCC *Actual CfD Generation and Avoided GHG Emissions* (already in `data/`) | 2a, 2b, 2c, 3a–3e, 6a, 6b, 7a |
| LCCC *CfD Register* (installed capacity, commissioning date) | 1a, 1b, 1c |
| Elexon / NESO wholesale prices | 4a, 4b |
| NESO BMRS constraint payments | 5a |
| UK ETS price series, DEFRA social cost of carbon | 3d overlay |

---

## Out of scope (for now)

- Renewables Obligation Certificate (ROC) revenues — separate subsidy regime, not in this dataset.
- Embedded benefits and network-charge avoidance for smaller plants.
- Capacity Market payments to backup gas.
- Lifecycle emissions accounting (manufacture, decommissioning) of renewable assets.

These should each be added as a later phase if the suite evolves from "CfD economics" into "all-in cost of the low-carbon transition."
