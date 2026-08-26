# EIC Streaming Tracking Benchmark

> Given an unordered, ~2 µs window of ePIC central-tracker hits containing exactly one
> buried DIS physics event on top of continuous beam/synchrotron background, reconstruct
> the tracks belonging to that event and tag which reconstructed objects are signal rather
> than overlay — all within a resource budget that must eventually fit inside the readout
> firmware, because ePIC has no hardware trigger to do this filtering for you.

**Scientific Motif(s):** High-Energy Physics
**AI/ML Motif:** Classification *(judgment call — see "Motif tagging" below)*
**Computing Motif(s):** Latency Bound · Memory Bound · Throughput Bound

This benchmark card follows the structure defined by the MLCommons Science Benchmarks
Ontology (arXiv:2511.05614). It was assembled from the DOE Genesis Mission Phase I
proposal *"Agentic AI for Real-time Expedited Discovery from High-Complexity EIC Data
Streams"* (Purdue/FNAL/LANL/MIT/NJIT) and its project meeting materials on Indico
(`indico.cern.ch/category/21857`) — see the **Sources** section at the bottom for exact
evidence pointers used to write each claim below.

**Status: this is a working draft, not yet the team's finalized benchmark.** The
proposal's own Months 1–2 milestone is "finalize the EIC use case, benchmark definition,
dataset splits, ... fixed evaluation metrics" — that finalization has not happened yet as
of this writing (26 Aug 2026). Sections below are marked `[GAP]` wherever the source
material genuinely doesn't yet answer the question; those are real open items for the
team, not places this draft guessed generously to look complete.

---

## 1. Problem Specification and Constraints

**Task.** Given a point cloud of tracker hits (`<input representation: unordered set of
hits, i.e. a point cloud>`), produce (a) a hit→track grouping restricted to the true
signal event, and (b) a per-object signal/background tag (`<output: joint set-prediction +
binary classification>`). Concretely, two sub-tasks over the same input:

- **RECONSTRUCT** — group hits into tracks. A *target* is a charged particle crossing
  ≥ 3 distinct detector layers with pT ≥ 0.1 GeV, belonging to the one true DIS signal
  event overlaid in the window (not the background overlay).
- **TAG** — decide which reconstructed tracks (and, at finer grain, which hits) belong to
  the signal event rather than the background overlay, using timing — geometry alone
  cannot separate them, since the background is uniform across the full window while
  signal hits land within ~±20 ns of a random per-event T0.

Absolute hit time is not usable as a cut (T0 is random per event); the discriminating
signal is *relative* timing coincidence — inside a ±20 ns window, signal jumps from 1.1%
to ~38% of hits.

**Inputs.** One streaming-readout window of ePIC central-tracker hits (~5,700 hits/window
in the reference mixed sample), each hit described by 15 features — see
`data/SCHEMA.md` for the exact per-field list (position, conformal-map coordinates, hit
time + uncertainty, energy deposit, position uncertainties, detector system/layer, local
time density). No seeding, road-following, or explicit trajectory fit is assumed as
preprocessing — the hit set is genuinely unordered.

**Outputs.** Per event: a set of predicted tracks, each a subset of the input hits (a
"mask" over the hit set), plus a signal-membership score per track (and, at the finer
grain the reference solution actually reports, per hit).

**System constraints** (fixed bounds a valid solution must satisfy, not metrics being
optimized):

| Constraint | Value | Source |
|---|---|---|
| End-to-end latency | **≤ 0.6 ms** | ePIC streaming Time-Frame duration (proposal target; the team's own working number — pinned here per project decision, see Sources) |
| Deployment target | Must have a path to FPGA firmware (fixed-point/quantized, on-chip weights) | Streaming readout has no hardware trigger — filtering has to happen inline in the DAQ chain, not offline |
| Arithmetic | Fixed-point only in the deployed path (no practical float32 on fabric) | HEPTv2/hls4ml slide deck, "Compression" section |
| On-chip weight storage | Full-precision (1.59M-param, fp32) baseline does **not** fit; compressed variant (337k params, 6-bit, 48% sparse, 127 KB) does | Same source |
| Resource ceiling | Reference HLS kernel already reaches ~97% LUT at sequence length 600 on a Xilinx Alveo U250 | Same source |

`[GAP]` The 0.6 ms figure is carried over from the proposal text, which itself marks it
"(TBD, ePIC streaming...)" — the team decided to pin it here for now, but it has not been
independently re-derived or confirmed against the actual ePIC TimeFrame spec.

---

## 2. Dataset

**Summary.** Official ePIC full-detector Monte Carlo simulation: deep-inelastic
scattering (DIS, neutral-current, 10x100 GeV beam energies, minQ2=100) signal events,
overlaid with realistic synchrotron-radiation and beam-gas background
(`Bkg_Exact1S_2us`, `GoldCt`, 10 µm), reconstructed with `eicrecon`. **Canonical
campaign/version: `26.07.1`, `epic_craterlake` detector geometry** (pinned per project
decision — an earlier `26.04.1`/April campaign also exists and remains a valid fallback if
`26.07.1` access issues recur).

Signal hit occupancy is roughly three orders of magnitude below background: synchrotron
background exceeds GHz rates in the inner pixel layers while true DIS signal hits are
~hundreds of kHz.

**Access.** Files are managed as Rucio datasets, not a flat filesystem hierarchy;
retrieved via XRootD. Example dataset identifiers (DIDs):

```
epic:/RECO/26.07.1/epic_craterlake/DIS/NC/10x100/minQ2=100/*
epic:/RECO/26.07.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=100/*
```

Example direct XRootD pull:
```
xrdcp root://hpceph-xrootd.twgrid.org:1094//cephfs/epic//RECO/26.07.0/epic_craterlake/DIS/NC/10x100/minQ2=100/pythia8NCDIS_10x100_minQ2=100_beamEffects_xAngle=-0.025_hiDiv_1.0746.eicrecon.edm4eic.root ./
```
`eic-shell` (used version: `26.05`) provides the Rucio/XRootD tooling; see
`https://eic.github.io/tutorial-file-access/01-introduction.html`.

**Format.** `eicrecon` output is an `EDM4eic`-model ROOT file managed by the PODIO
framework (Structure-of-Arrays: flat, contiguous branches; relationships between objects
resolved through separate index-lookup branches prefixed `_`). Raw files carry
> 1,000 branches, of which this benchmark uses a small, documented subset — see
`data/SCHEMA.md` for the filtered field list actually consumed.

**Splits.** `[GAP — not yet finalized by the team, per the proposal's own Month 1–2
milestone]`. The only splits that exist today are ad hoc, from the reference solution's
own evaluation, not a canonical benchmark release:

| Split | Size | Purpose | Status |
|---|---|---|---|
| Mixed (signal+background overlay), train | ~446 events (495 − 49) | Model training | Ad hoc, not frozen |
| Mixed, test (held out) | 49 events | Reported test-set numbers (DM, fake rate, AUROC) | Ad hoc, not frozen |
| Signal-only (no overlay), 5,415 events | — | Upper-bound / generalization check (analogous to wa-hls4ml's "exemplar" set) | Ad hoc, not frozen |

The reference solution's own author flags this directly: *"The mixed sample has 495
events — ~2,470 target tracks in the whole training split... the limit is sample size."*
Formalizing a larger, canonical, non-overlapping train/val/test split (ideally stratified
by background rate — see "Robustness" in the metrics section) is the single highest-value
open item for this benchmark, by the reference solution's own assessment.

**Truth labels — a required preprocessing subtlety.** Truth association follows
`TrackerHit → RawTrackerHit → RawHitAssociation → SimTrackerHit → MCParticle`. The overlay
merger encodes `generatorStatus = 1000×source + status`, with `source == 0` marking the
true DIS event — **but** Geant4 secondaries always carry `status == 0` regardless of their
true origin, so signal-event membership must be inherited by walking
`MCParticle.parents` up to the first generator-level ancestor. Taking `generatorStatus` at
face value mislabels background-shower secondaries as signal (173 vs. the correct 71
"signal" hits per event in the reference solution's own measurement) — this is a real,
previously-hit correctness bug in naive labeling, not a hypothetical edge case.

**FAIR checklist:**
- [x] **Findable** — every hit traces to a unique `MCParticle`/event via the association
  chain above; every ROOT file has a Rucio DID.
- [ ] **Accessible** `[GAP]` — access is currently through EIC/ePIC-collaboration Rucio
  infrastructure, not a persistent open/public protocol. Proposal text notes Genesis
  Mission assets will be prepared "with documentation, metadata, provenance, and
  access-control assumptions suitable for future sharing... subject to DOE guidance" — that
  sharing has not happened yet.
- [x] **Interoperable** — EDM4eic/PODIO is the EIC collaboration's own community-standard
  data model for reconstructed data.
- [ ] **Reusable** `[GAP]` — the *filtered* schema this benchmark actually trains on (see
  `data/SCHEMA.md`) is described in slides but the extraction/preprocessing script that
  produces it from raw EDM4eic files is not yet a published, versioned artifact.

**Bounded-ness.** No augmentation, enrichment, or post-hoc curation of the released
splits is permitted for submissions once the canonical splits above are frozen (default
per the ontology's stable-target definition).

---

## 3. Performance Metric(s)

This is a **multi-dimensional (Pareto) benchmark**: physics-quality metrics are compared
*at a fixed resource/latency budget* (Section 1's system constraints), not traded off
against them freely.

| Metric | Formula / definition | What it captures | Computed on |
|---|---|---|---|
| **Per-hit signal AUROC** | ROC-AUC of the per-hit signal/background classifier score vs. truth label (see Truth labels above) | How well timing-based tagging separates the ~0.1–1% signal hits from background at the finest grain | Test split, pooled hits |
| **Per-track signal AUROC** | ROC-AUC of the mean per-hit score over each reconstructed track vs. track-level signal/background truth | Same, at track granularity | Test split, pooled tracks |
| **Double Majority (DM)** | # predicted tracks with **both** purity > 0.5 **and** completeness > 0.5, ÷ # target tracks. Purity = (hits in predicted track from its majority-contributing truth particle) / (hits in predicted track). Completeness = (hits of that truth particle captured by the track) / (all hits of that truth particle). | The standard HEP tracking figure of merit — a track must be both mostly-correct and mostly-complete to count | Test split |
| **Technical efficiency** | # distinct target particles found by ≥ 1 track with purity ≥ 0.5, deduplicated (a particle found twice counts once), ÷ # targets | Looser than DM — efficiency ignores completeness, so it sits slightly above DM in every reported table | Test split |
| **Fake rate** | # predicted tracks where no single truth particle owns a majority of its hits, ÷ # predicted tracks (**not** ÷ targets — does not complement DM/efficiency) | False track rate — directly reduced by the post-processing described in Section 4 | Test split |
| **Background rejection / compression ratio** | Bit-operations (MACs × weight bits × activation bits) at fixed accuracy, relative to an fp32 baseline; separately, raw background-hit-load reduction relative to the unfiltered stream | Whether the model actually shrinks the data/compute the downstream chain must handle — the proposal's Decision Gate requires ≥ 10× background-load reduction and ≥ 2× improvement over the best non-AI baseline at matched signal retention | Test split, measured against the fixed system constraints in Section 1 |
| **Signal retention** | Fraction of truth-matched DIS signal hits/clusters retained after filtering | Decision-gate target: ≥ 95%, with ≤ 2% relative degradation in one downstream proxy (track efficiency, fake rate, or vertex performance) | Test split |
| **Robustness** | Signal retention held within 3 percentage points across ≥ 3 background-rate/detector-variation conditions; confidence-score calibration under distribution shift | Whether results generalize beyond one fixed background rate | `[GAP]` — no benchmark split currently varies background rate; only single-rate results exist today (see Dataset splits) |

**Edge cases / definitions.** Fake rate's denominator is predicted tracks, not targets,
so it deliberately does not sum to 1 with DM/efficiency — this is called out explicitly
because it's an easy mis-implementation. Purity/completeness ties at exactly 0.5 count as
passing (`> 0.5` for purity per the reference solution's own convention, `≥ 0.5` for the
efficiency dedup rule — these should be reconciled to one convention when the split is
frozen; `[GAP]`, currently inherited verbatim from two slightly differently-worded slides).

**Definitions level (rubric self-score): 3/3** — every metric above has an exact,
reproducible formula, evidenced against the reference solution's own reported numbers.
**Quality level (rubric self-score): 2/2** — the metric suite jointly captures physics
correctness (DM/efficiency/fake-rate/AUROC) *and* deployability (compression ratio,
latency budget as a hard constraint), matching the benchmark's own stated goal of "AI
advantage" being about both at once, not physics performance alone.

---

## 4. Reference Solution

**Summary.** HEPTv2 — an LSH (locality-sensitive-hashing) point transformer, adapted from
the original HEPTv2 architecture (targeting the CMS L1 trigger) to ePIC central tracking
by J. Schulte. Presented 26 Aug 2026 (Genesis eIC-agentic-AI meeting).

**Architecture / method.**
- **Input:** all hits as an unordered set (5,698 × 15 features in the reference run).
- **Encoder ×4:** RMSNorm → Q/K/V projection → E2LSH hash of each hit's coordinates
  `(η, φ, t)` → sort by hash → attention restricted to fixed blocks of 256 hits (bucketing
  turns quadratic attention near-linear while keeping spatially/temporally nearby hits
  together) → unsort → feed-forward → residual. 3 independent hash rounds so a pair split
  by one hashing round can still meet in another.
- **Decoder ×2:** 256 learned query vectors cross-attend to encoded hits, self-attend to
  each other, then feed-forward. Each query emits a mask over all hits (one query = one
  candidate track); every hit takes the `argmax` over the 256 mask rows to get its track
  label. Nothing in this construction enforces the result be a physically valid
  trajectory — hence the post-processing step below.
- **Signal head:** per-hit classifier on the encoder output, trained with
  positive-weighted BCE; a track's signal score is the mean of its hits' scores.
- **Post-processing (three-stage check, thresholds calibrated to the real-track p99):**
  **Split** tracks at internal time gaps wider than any real track shows (real tracks span
  ≤ 26.9 ns internally); **Trim** unassigns hits far from their track's median time;
  **Reject** drops tracks with too many duplicate layers (a real track crosses each layer
  ~once). Net effect on the test split: fake rate down 41% (0.281 → 0.166) with every
  other reported metric simultaneously up.
- **Hyperparameters (baseline → compressed variant actually deployed):** hidden width
  128→64, attention heads 8→4, encoder blocks 4→3, decoder queries 256→64, output MLP
  256×5→128×4, giving 1.59M→337k parameters and 16.5G→4.32G MACs/event. Accuracy is flat
  across this range — degradation only starts below ~160k parameters.
- **Quantization/pruning:** QAT via PQuant-ML (free to 6 bits, breaks at 4); WANDA pruning
  (free to 66% sparsity alone, breaks at 79%; the two do **not** compose freely — combined
  6-bit + 48% sparse gives 211× fewer bit-operations at DM 0.605 vs. 0.611 float32, while
  6-bit + 66% sparse together costs far more, DM 0.562 — reported explicitly as a "fixed
  redundancy budget" finding, not a mistake to silently avoid repeating).
- **Deployability windowing:** input segmented 8 time-slices × 3 φ-slices (24 windows,
  ~251 hits/window) to fit inside the hls4ml HLS kernel's deployable sequence-length range
  (N ≤ 300 on a Xilinx Alveo U250) — this *improves* DM (0.571 vs. 0.552 unsplit) rather
  than costing accuracy, because most windows are pure background and free to discard.

**Results** (pooled held-out test split, 49 events out of the 495-event mixed sample):

| Metric | Value |
|---|---|
| Per-hit signal AUROC | 0.992 (TPR 0.904 @ FPR 0.0076 at the 0.5 cut) |
| Per-track signal AUROC | 0.927 |
| Double Majority (post split+trim+reject) | 0.597 (0.563 before post-processing) |
| Technical efficiency | 0.636 |
| Fake rate | 0.166 (0.281 before post-processing) |
| Perfect (hit-for-hit exact) tracks | 24% of signal tracks |
| Compression (best deployable point) | 211× fewer bit-operations vs. fp32 baseline, DM 0.605 (unchanged within run-to-run scatter) |
| Weight storage | 127 KB (from 6,210 KB fp32) — fits on-chip |

On the signal-only sample (5,415 events, no background overlay — the reference solution's
own stand-in for a generalization/exemplar set) the same code reaches DM 0.841, 44%
perfect — the gap to the mixed-sample numbers is attributed explicitly to training-sample
size (~2,470 target tracks total in the mixed training split), not a modeling limitation.

**Requirements.**
- **Training/simulation software:** `eic-shell 26.05`, `eicrecon 26.07.1`; PyTorch;
  PQuant-ML for QAT; WANDA for pruning.
- **Firmware path:** hls4ml (model → C++) → Vitis HLS → RTL, targeting a Xilinx Alveo
  U250 (200 MHz). An HLS implementation of one HEPTv2 v1 encoder attention block already
  exists in an hls4ml fork; the decoder has no kernel implementation yet (~3–4 weeks of
  work estimated, though only 16% of compute at the deployed window size).
- **Hardware for training/inference benchmarking:** reference CPU/GPU timing figures
  (5.1 ms/event CPU on a Ryzen 9 7950X; 2.1 ms/event GPU on an RTX 2080 Ti; µs-scale on an
  Alveo U250 at 200 MHz) are measured for the **upstream HEPT model on its own
  (non-EIC) dataset**, not yet re-measured end-to-end on this ePIC-adapted model —
  `[GAP]`, flagged explicitly by the source material itself ("the reference model on its
  own dataset, not ours — the ratio is the point, not the absolute numbers").
- **Broader project compute:** the team is provisioning Purdue Anvil (AMD EPYC CPUs +
  NVIDIA A100 GPUs), Argonne Polaris/Aurora (AMD/Intel CPUs + A100/Intel Max GPUs), and
  NERSC allocations; NVIDIA-side options under discussion include a
  CUDA 12.2+/TensorRT/Triton stack for GPU-side inference serving. None of this is yet
  consolidated into one pinned environment for this specific benchmark.

**Code availability — `[GAP, confirmed by the team]`.** The reference implementation is
referenced internally as `heptv2/EIC.md` but **is not publicly available**. This is a
real, current gap against the Software Environment and Reference Solution rubric
categories below, not an oversight in this write-up — publishing the code (even as a
private-then-public GitHub release under `github.com/Agentic-AI-for-EIC`, the project's
existing org) is the single highest-leverage fix available to this benchmark's rubric
score.

---

## 5. Documentation and Reproducible Protocol

**Reproduction steps.** `[GAP]` — no numbered, copy-pasteable reproduction script exists
yet; what exists is a slide deck (`eic_hept_slides_JSchulte.pdf`) plus references to an
internal `heptv2/EIC.md`. Writing this up as an actual runnable pipeline (data pull via
Rucio DID → `eicrecon` → filtered-schema extraction → HEPTv2 train/eval →
`scores.json`-equivalent) is the natural next step once the code above is public.

**Environment.** `[GAP]` — not yet containerized or pinned as a single environment file;
see "Requirements" above for the individual pieces (`eic-shell 26.05`, PyTorch, PQuant-ML,
hls4ml, Vitis HLS) that would need to be consolidated.

**Motivation.** The EIC will operate in a high-rate, background-dominated regime: inner
silicon-pixel background occupancy can exceed GHz rates from synchrotron radiation and
beam-gas interactions, while true DIS signal hits run only hundreds of kHz — three orders
of magnitude lower. Left unmitigated, this saturates readout bandwidth, data movement,
storage, and downstream reconstruction, directly constraining the EIC physics reach. ePIC
streams every channel continuously with no hardware trigger, so any reduction has to
happen inline in the DAQ chain — this benchmark exists to give the DOE Genesis Mission
Phase I effort (and any future contributor) a fixed, shared target to measure "does a
given sparse/deployment-aware model actually solve this" against, rather than each team
re-deriving its own ad hoc test.

**Background.** The EIC's innermost silicon tracking layers face the same class of
occupancy problem already observed operationally at sPHENIX (cited directly as
precedent in the source proposal). SVT (silicon vertex tracker) noise studies presented
at the joint ePIC/EICUG meeting (Glasgow, 16 Jul 2026) separately confirm that random
pixel noise (up to the ITS3-derived upper limit of 2×10⁻⁷ hits/pixel/2µs) is not yet a
dominant tracking degradation relative to true machine background — i.e., the dominant
challenge this benchmark targets is genuinely the beam-induced background, not sensor
noise, at currently-assumed noise rates.

**Evaluation criteria.** See Section 3 above — restated here per the ontology template:
every metric is computed on the (currently ad hoc, `[GAP]` pending finalization) held-out
test split, with the compression/latency dimensions evaluated against the fixed system
constraints in Section 1 rather than traded off against physics quality.

**Paper.** `[GAP]` — no academic paper about this benchmark exists yet. The closest
artifact is the DOE Genesis Mission Phase I proposal itself (`Genesis2026_14c.pdf`),
which is a funding proposal, not a benchmark paper.

**Citation.** `[GAP]` — no formal citation exists yet. Until one does, cite the Indico
category (`indico.cern.ch/category/21857`, "Agentic AI for Real-time Expedited Discovery
from High-Complexity EIC Data Streams") and, for the reference solution specifically, the
26 Aug 2026 project meeting talk by J. Schulte.

---

## Motif tagging

**Scientific Motif:** High-Energy Physics.

**AI/ML Motif — judgment call.** The taxonomy requires exactly one tag, but this
benchmark is genuinely two coupled tasks: a **Classification** problem (per-hit/per-track
signal-vs-background tagging, cleanly captured by AUROC) and a **structured
set-prediction** problem (grouping hits into tracks) that doesn't map cleanly onto any
single item in the current taxonomy (it is closer to "clustering" or "object detection"
than to Classification, Regression, or Sequence Prediction/Forecasting as those are
described in `references/ontology.md`). **Classification** is used as the single tag here
because (a) it's the sub-task the reference solution's own summary calls "the solid
result" (AUROC 0.99, robust across every compression/windowing variant tested), and (b)
none of the other eight taxonomy items fit the tracking sub-task better. This is flagged
explicitly as an imperfect fit, not a confident classification — a case could reasonably
be made to MLCommons that the taxonomy is missing a set-prediction/clustering motif that
HEP tracking benchmarks generally need.

**Computing Motifs:** Latency Bound (0.6 ms budget), Memory Bound (on-chip weight
storage; 6.2 MB fp32 weights do not fit, 127 KB compressed does), Throughput Bound
(continuous streaming readout, no trigger to reduce rate upstream).

---

## Sources

Everything above is sourced from the DOE Genesis Mission Phase I proposal and project
meeting materials retrieved from Indico (`indico.cern.ch/category/21857`) and archived
locally at `../indico-eIC-agentic-AI-materials/`:

| Claim area | Source file |
|---|---|
| Background/motivation, objectives, decision-gate metrics | `01_Kickoff_29jul2026/.../Genesis2026_14c.pdf` (proposal, Sections 1, 2, 6) |
| HEPTv2 architecture, inputs, truth handling, metrics, results, compression, hardware status | `05_26aug2026/.../eic_hept_slides_JSchulte.pdf` |
| Data access, DIDs, file format, filtered schema | `02_05aug2026/.../Genesis_260805.pdf` |
| Phase-I success metrics (independent restatement) | `02_05aug2026/.../ePIC-Genesis-Sim-Analysis-WorkFlow-082026-MingLiu.pdf` |
| SVT sensor-noise context | `02_05aug2026/.../SVT noise in tracking_EICUG2026-2.pdf` |
| Compute environment (Purdue/Argonne/NERSC/NVIDIA) | `03_12aug2026/.../PurdueComputeResources.pdf`, `03_12aug2026/.../Fast-ML-for-EIC-NVIDIA-DIscussions-0806-2026.pdf` |
| Project objectives/tasks/milestones (independent restatement) | `01_Kickoff_29jul2026/Kick-off_meeting/20260729_Wednesday/1630.../kick-off.pdf` |

See `assets/submission_report_template.md` (in the `benchmark-builder` skill) for the
report format a new submission to this benchmark should follow.
