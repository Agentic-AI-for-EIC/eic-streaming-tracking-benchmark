# EIC Streaming Tracking Benchmark — Benchmark Card

Condensed benchmark card in the MLCommons Science Benchmarks Ontology structure
(arXiv:2511.05614). The full, evidence-cited version is `README.md`; where they differ,
`README.md` wins. Working draft, 2026-09-25.

**Scientific Motif(s):** Nuclear Physics · **AI/ML Motif:** Classification (judgment call)
· **Computing Motif(s):** Latency Bound · Memory Bound · Throughput Bound

## 1. Problem Specification and Constraints

**Task.** Given an unordered ~2 µs window of ePIC central-tracker hits containing, on
average, one buried DIS physics event on top of continuous beam/synchrotron background,
reject background hits while keeping the signal event's tracks.

**Inputs.** One streaming-readout window of tracker hits (~5,700 hits, 15 features/hit;
`data/SCHEMA.md`). No seeding or trajectory fit assumed.

**Outputs.** Per hit/track signal-vs-background decision (plus optional tracks).

**System constraints.** End-to-end latency ≤ 0.6 ms (proposal working number, pinned by
project decision). Approximate input rate ~342 KB/window, ~1.4 Tb/s (~171 GB/s),
computed, not sourced. The hardware is deliberately not fixed.

## 2. Dataset

ePIC full-detector MC, April 2026 campaign `26.04.1`, `epic_craterlake`: DIS NC 10x100,
minQ2=100 with `Bkg_Exact1S_2us` overlay. Rucio/XRootD access (collaboration credentials).
Splits are not frozen: ad hoc mixed 446 train / 49 test, plus 5,415 signal-only events.
Full detail and gaps: `DATA_CARD.md`.

- [x] Findable · [ ] Accessible (collaboration-gated) · [x] Interoperable (EDM4eic) ·
  [ ] Reusable (extraction script unpublished)
- Bounded: no augmentation once splits are frozen.

## 3. Performance Metric(s)

| Metric | Definition | Target |
|---|---|---|
| Background hit rejection factor | background hits in ÷ background hits passing the filter | as large as possible; ≳ 2× |
| Signal track retention rate | fraction of target signal tracks (≥3 layers, pT ≥ 0.1 GeV) retained | ~100% |

Reported as a pair: rejection factor at a given retention. `[GAP]` the exact "retained"
criterion is not pinned.

## 4. Reference (Baseline) Solution

Kalman Filter tracking: EICrecon rule-based central tracking (ACTS seeding + CKF), public,
LGPL-3.0. **UNCONFIRMED and not run**, so no results. See `MODEL_CARD.md`,
`reference_solution/README.md`. HEPTv2 is an AI comparison entry (slide-deck results only).

## 5. Documentation and Reproducible Protocol

No run recipe or pinned environment yet (`requirements.txt` is a partial sketch).
Scoring: `metrics/score.py`. Submissions: `SUBMISSION.md`. Sources: `README.md` Sources.
Citation: none formal; cite Indico category 21857 for now.

## Open items

Freeze splits; run and document the baseline; pin the "retained" criterion; publish the
extraction script; confirm license, identifiers, and contacts (see `DATA_CARD.md`).
