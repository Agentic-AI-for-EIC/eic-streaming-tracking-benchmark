# Reference Solution: EICrecon rule-based central tracking (ACTS seeding + CKF)

**Status: UNCONFIRMED.** The reference is the standard rule-based (non-AI) track
reconstruction in the ePIC software stack, **EICrecon**. It was named as the reference by
the benchmark owner and located via public GitHub/tutorial pages only. **It has not been
cloned, built, or run for this benchmark**, and the algorithm details below (ACTS seeding
followed by a Combinatorial Kalman Filter) come from the owner's description plus general
knowledge of EICrecon, not from reading its source. Every item marked `[UNCONFIRMED]` must
be checked against the EICrecon code/config before this benchmark is presented as verified.

## What it is

EICrecon (`https://github.com/eic/EICrecon`, LGPL-3.0, docs at
`https://eic.github.io/EICrecon/`) is the JANA2-based reconstruction framework for the ePIC
detector. Its central tracking is a conventional, rule/domain-based chain: hits are grouped
into seeds, and tracks are then followed and fit with a Kalman-filter-based method
(`[UNCONFIRMED]`: ACTS seeding + CKF; exact algorithms, source paths, and configuration
parameters not yet read).

## Role in this benchmark

- **It is the accuracy reference, not a deployable solution.** It does not meet the
  benchmark's bandwidth/latency constraints (`README.md` Section 1: 0.6 ms latency,
  ~1.4 Tb/s streaming input, fixed-point FPGA path). Its job is to show what a
  physics-complete, rule-based reconstruction achieves on the same data, so AI submissions
  can be compared to it at matched signal retention (the proposal's Decision Gate asks for
  a ≥ 2× improvement over the best non-AI baseline).
- **It needs no training.** There are no learned weights, so "training code" and
  "hyperparameters" reduce to the algorithm's configuration parameters.
- **Output format:** EDM4eic/PODIO ROOT files (`*.eicrecon.tree.edm4eic.root`), which is
  what `metrics/score.py` and `data/SCHEMA.md` already assume. The public
  `github.com/eic/tutorial-analysis` lesson shows how to read these with ROOT, uproot, and
  RDataFrame and is a template for the scoring I/O (it is analysis tutorial content, not a
  reconstruction or scoring pipeline).

## How to obtain and run  `[UNCONFIRMED — not yet run]`

Per the EICrecon README (build steps not executed here):

```
cmake -B build -S . -DCMAKE_INSTALL_PREFIX=install
cmake --build build
cmake --install build
source install/bin/eicrecon-this.sh
```

Normally used inside `eic-shell`. The data-production chain
(npsim/Geant4 simulation → EICrecon → EDM4eic output) is covered by the public ePIC
tutorials (`https://eic.github.io/tutorial-simulations-using-npsim-and-geant4/`,
`https://eic.github.io/tutorial-jana2`). Benchmark-specific instructions (which config,
which collections, how to convert to the 15-feature-per-hit schema and back to scored
tracks) are `[GAP]`.

## Requirements

- **Software:** `eic-shell` and `eicrecon` (campaign versions used for the dataset:
  `eic-shell 26.05`, `eicrecon 26.07.1` per the project materials; `[UNCONFIRMED]` that
  these are the versions to pin for the reference run).
- **Hardware:** CPU-based; specific CPU/memory requirements and per-event latency for the
  benchmark's mixed signal+background events are `[GAP]` (not measured).

## Results

**None yet.** The reference's per-hit / per-track AUROC, Double Majority, technical
efficiency, fake rate, and latency on this benchmark's data have not been computed. They
require running EICrecon on the benchmark's mixed-background samples and scoring with
`metrics/score.py`. Until then, do not cite any number as the reference result.
Note the Robustness metric also has no reference value.

## Earlier reference candidate: HEPTv2 (now a comparison/submission entry)

The benchmark was originally drafted with HEPTv2 (J. Schulte, 26 Aug 2026 Genesis
eIC-agentic-AI meeting) as the reference. HEPTv2 is an LSH point transformer, adapted from
CMS L1-trigger HEPT, that performs RECONSTRUCT and TAG jointly, aimed at the FPGA
constraints. Its code is not public, so it is not suitable as the reference. It stays in
this benchmark as an AI comparison point, with the figures it reported (from the slide
deck, not independently reproduced):

| Metric (held-out 49 of 495 mixed events) | HEPTv2 reported |
|---|---|
| Per-hit signal AUROC | 0.992 |
| Per-track signal AUROC | 0.927 |
| Double Majority (post-processed) | 0.597 |
| Technical efficiency | 0.636 |
| Fake rate | 0.166 |
| Bit-operations reduction vs. fp32 | 211× (compressed variant: 337k params, 6-bit, 48% sparse, 127 KB) |

Signal-only sample (5,415 events): DM 0.841, 44% perfect tracks. Architecture: 4 encoder
blocks (RMSNorm, E2LSH hash on (η,φ,t), attention within 256-hit blocks), 2 decoder blocks
with 256 learned queries emitting per-hit masks, per-hit signal head, and split/trim/reject
post-processing; baseline 1.59M params, 16.5 GMACs/event. Latency figures in the deck are
for upstream HEPT on its own dataset, not this model. FPGA decoder kernel not built. Source
material: `eic_hept_slides_JSchulte.pdf`.

## Known limitations

- Everything under "How to obtain and run", "Requirements" and "Results" is unverified.
- The rule-based reference is not built for the streaming latency/bandwidth constraints, by
  design; comparing against it says how much accuracy an AI model gives up (or keeps) when
  it meets them.
- The split/sample definitions used for any reference run are not yet frozen
  (`README.md` Dataset Splits).
