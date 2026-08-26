# Data Schema

Two schema layers exist: the raw `eicrecon` output (source), and the filtered per-hit
schema this benchmark actually trains/evaluates on (derived). Both are documented here so
a submitter can either start from the filtered schema directly or re-derive it from raw
files.

## Raw source

- **Framework:** PODIO (Structure-of-Arrays: flat, contiguous branches; relationships
  between objects — e.g. hit → contributing MC particle — resolved via separate
  index-lookup branches, named with a leading `_`).
- **Data model:** EDM4eic.
- **File format:** ROOT, produced by `eicrecon`.
- **Size:** raw files carry > 1,000 branches/collections; this benchmark uses a small
  documented subset (below).
- **Access:** Rucio DID → XRootD. See `README.md` Section 2 for example DIDs and pull
  command. `[GAP]`: access currently requires EIC/ePIC-collaboration Rucio credentials —
  not yet a public/open protocol.

## Filtered per-hit schema (what the reference solution trains on)

One row per hit, grouped by event:

| Field | Description | Source (raw) |
|---|---|---|
| `event_id` | Event identifier within the file | event header |
| `collection` / `subdetector` | Which tracker sub-collection the hit belongs to (silicon vertex, silicon barrel, silicon endcap, MPGD barrel/endcap, TOF where present) | collection name |
| `cellID` | Encodes detector `system` and `layer` (decode to get columns 12–13 below) | `TrackerHit.cellID` |
| `x, y, z` | Global hit position | `TrackerHit` position |
| `edep` (or charge) | Deposited energy/charge at the hit | `TrackerHit.edep` |
| `t`, `timeError` | Hit time and its uncertainty | `TrackerHit.time`, `.timeError` |
| MC truth: particle index | Index into `MCParticle` collection | `TrackerHit → RawTrackerHit → RawHitAssociation → SimTrackerHit → MCParticle` |
| MC truth: PDG code | Truth particle species | `MCParticle.PDG` |
| MC truth: generator status | **Do not use at face value — see Truth-label subtlety below** | `MCParticle.generatorStatus` |
| MC truth: production vertex | Where the truth particle originated | `MCParticle` |

### Truth-label subtlety (required preprocessing step)

The overlay merger writes `generatorStatus = 1000×source + status`, with `source == 0`
identifying the true DIS event. **Geant4 secondaries always carry `status == 0`
regardless of their true origin** — so signal-event membership must be inherited by
walking `MCParticle.parents` up to the first generator-level ancestor, not read directly
off `generatorStatus`. Skipping this step measurably mislabels background-shower
secondaries as signal (173 vs. the correct 71 "signal" hits/event in the reference
solution's own before/after measurement).

Where a raw hit has multiple sim-hit contributors (~30% of hits in the reference sample),
the highest-weight contributor determines the hit's truth label. Zero hits are left
unmatched under this rule.

## Model input features (15 columns per hit)

This is the exact feature vector the HEPTv2 reference solution consumes — derived from
the filtered schema above, not a raw-file 1:1 mapping:

| Col(s) | Feature | Notes |
|---|---|---|
| 0–3 | `r, φ, z, η` | Geometric position, cylindrical + pseudorapidity |
| 4–5 | `u, v` | Conformal-map coordinates — a circular track through the beamline becomes a straight line in this representation |
| 6–7 | `t, timeError` | Hit time and its uncertainty |
| 8 | `log₁₀(edep)` | Log-scaled energy deposit |
| 9–11 | `σₓ, σy, σz` | Position uncertainties |
| 12–13 | `system, layer` | Decoded from `cellID` |
| 14 | `t_density` | Hits within ±25 ns of this hit, normalized to the uniform-background expectation — a local timing-coincidence feature |

Separately from these 15 features, each hit also carries a 3-vector `(η, φ, t)` used
*only* for LSH bucketing (attention locality), not as a model input feature in the usual
sense.

## Target definition

A target track = a charged particle crossing ≥ 3 distinct detector layers with
pT ≥ 0.1 GeV, belonging to the one true signal event in the window (see Truth-label
subtlety above for how "belonging to the signal event" is actually determined). In the
reference mixed sample this yields ~6.2 targets/event out of ~18 reconstructable
particles/event.

`[GAP]`: the extraction script that turns raw EDM4eic files into this filtered schema is
not yet a published, versioned artifact — see `README.md` Dataset → Reusable (FAIR).
