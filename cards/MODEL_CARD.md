---
language:
- en
tags:
- project:genesis
- project:eic-streaming-tracking
- type:model
- science:nuclear-physics
- risk:general
license: LGPL-3.0-or-later # EICrecon; UNCONFIRMED against the repo's LICENSE file
datasets:
    - epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=100/* # Rucio DID, see DATA_CARD.md
metrics:
    - background hit rejection factor
    - signal track retention rate
---

# EICrecon Kalman Filter Tracking (Baseline)

Baseline solution for the EIC Streaming Tracking Benchmark: the standard rule-based
(non-AI) central tracking in EICrecon, ACTS seeding followed by a Combinatorial Kalman
Filter (CKF). **This is not a trained model** — it has no weights, training data, or
training procedure, so those template sections are marked N/A below.

**Status: UNCONFIRMED.** Not yet built or run for this benchmark. The algorithm
description comes from the project owner's description and general knowledge of
EICrecon, not from reading its source. No benchmark results exist yet.

*Last Updated*: **2026-09-25**

Format follows the DOE GEAR Model Card template v1 (`gear.doe.gov`, fetched 2026-09-25).

## Developed by

EICrecon / ePIC software collaboration (`https://github.com/eic/EICrecon`). Not developed
by this benchmark's team.

## Contributed by

Benchmark packaging by the Agentic AI for EIC team (Purdue/FNAL/LANL/MIT/NJIT).

## Model Changelog

+ **2026-09-25** first card; baseline named, nothing run.

## Model short description

Rule-based ACTS-seeding + Combinatorial Kalman Filter track reconstruction; the accuracy
baseline that AI submissions are compared against.

## Model description

Hits are grouped into seeds; tracks are then followed and fit with a Kalman-filter-based
method inside the JANA2-based EICrecon framework (`[UNCONFIRMED]`: exact algorithms,
source paths, and configuration). It is an accuracy baseline, not a deployable one: stock
EICrecon takes ~607 ms per event on one CPU thread (preliminary; source and caveats in
`README.md` Sources), about 1000× over the 0.6 ms budget.

## Model Type

Rule-based / classical tracking (seeding + Kalman filter). Non-ML.

## Inputs and outputs

- **Input:** EDM4eic/PODIO tracker hits from an ePIC simulation window (~2 µs, ~5,700
  hits/window in the reference mixed sample). See `data/SCHEMA.md`.
- **Output:** reconstructed tracks (EDM4eic/PODIO ROOT, `*.eicrecon.tree.edm4eic.root`).

## Compute Infrastructure

### Hardware

CPU. ~607 ms/event on one CPU thread in the 15 Jul 2026 study (preliminary, different
campaign). No DOE resource confirmed for a benchmark run.

### Software

`eic-shell 26.05`, `eicrecon 26.07.1` per project materials (`[UNCONFIRMED]` as the
reference-run versions; the benchmark dataset is now the April `26.04.1` campaign, so the
matching versions need checking). No pinned environment file exists yet.

## Papers and Scientific Outputs

No benchmark-specific paper. EICrecon: `https://github.com/eic/EICrecon`,
docs `https://eic.github.io/EICrecon/`.

## Model License

EICrecon is public and LGPL-3.0 (`[UNCONFIRMED]` against the repository's LICENSE file).

## Contact Info and Model Card Authors

nhanvtran (nhan.v.tran@gmail.com), the benchmark contact listed in
`mlcommons_corpus_entry.yaml`. **Confirm** this is the intended contact.

# Intended Uses

## Intended Use

Accuracy reference for the two benchmark metrics (background hit rejection factor, signal
track retention rate), against which AI background-filtering submissions are compared.

### Primary Intended Users

Researchers building or evaluating AI hit/track filters for ePIC streaming readout.

### Mission Relevance

DOE Genesis Mission Phase I project "Agentic AI for Real-time Expedited Discovery from
High-Complexity EIC Data Streams".

## Out-of-Scope Use Cases

Not for real-time deployment in the streaming DAQ chain: it does not meet the 0.6 ms
latency or bandwidth constraints.

# How to use

## Install Instructions

`[GAP]` No benchmark run recipe exists. Build/run steps are in the EICrecon README and the
public ePIC simulation tutorials; see `reference_solution/README.md`.

## Training configuration

N/A. No training.

## Inference configuration

`[GAP]` Exact EICrecon tracking configuration for the benchmark not yet pinned.

# Code snippets of how to use the model

`[GAP]` To be added once a run recipe exists.

# Limitations

## Risks

None identified beyond general software risks; no national-security-relevant capability.

## Limitations

- Not run: no metrics, so accuracy claims cannot be made.
- Per-event latency is far above the streaming budget.
- Timing figure comes from a different campaign (26.07.0, 10x275, minQ2=1000).

# Training details

N/A. Rule-based, no learned parameters, no training data.

# Evaluation details

## Evaluation data

April `26.04.1` `epic_craterlake` DIS NC 10x100 minQ2=100 with `Bkg_Exact1S_2us` overlay;
see `DATA_CARD.md`. Splits are not yet frozen.

## Evaluation Procedure

Score with `metrics/score.py`: background hit rejection factor and signal track retention
rate (definitions in `README.md` Section 3).

## Uncertainty Quantification

`[GAP]` None defined; the rule-based baseline is deterministic, but sampling variance over
events is not yet quantified.

## Evaluation results

None. Not yet run.

# More Information

AI comparison entry: HEPTv2 (LSH point transformer adapted from CMS L1-trigger HEPT);
slide-deck results only (see `README.md` Section 4).
