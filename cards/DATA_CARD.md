# EIC Streaming Tracking Dataset — Data Card

Structured against the **Genesis Mission Data Card v1.2** outline, following the pattern in
the benchmark-builder skill's `examples/wa-hls4ml/DATA_CARD.md`. The official generator
(`AI-ModCon/BaseData_Skills`, `datacard-generator`) was **not run**: no directory
introspection and no live ORCID/ROR/DOI/OSTI verification. This is a hand-filled draft;
unverified fields are flagged rather than asserted. Assembled 2026-09-25.

## `supports_*` capability flags

| Flag | Value | Why |
|---|---|---|
| `supports_discoverability` | Yes | Always required |
| `supports_accessibility` | Yes | Rucio/XRootD access (restricted, see below) |
| `supports_interoperability` | Yes | EDM4eic/PODIO is the ePIC community data model |
| `supports_reusability` | No | Filtered-schema extraction script not published; splits not frozen |
| `supports_governed_use` | Unknown | Access needs ePIC-collaboration credentials; no other regime identified. Needs human decision |
| `supports_ai_usability` | Yes | Built as an ML training/evaluation source |

## Discoverability [REQUIRED]

- `name`: ePIC streaming tracking, DIS NC 10x100 with synchrotron/beam-gas overlay
- `version`: April 2026 campaign `26.04.1`, `epic_craterlake` geometry
- `id`: none assigned. **Flag:** no ARK/OSTI DOI minted; check whether one should be.
- `template_version`: 1.2; `creation_method`: Hybrid (manual from repo docs, no introspection)
- **Description.** Official ePIC full-detector Monte Carlo: neutral-current DIS
  (10x100 GeV, minQ2=100) signal overlaid with synchrotron-radiation and beam-gas
  background (`Bkg_Exact1S_2us`, `GoldCt`, 10 µm), reconstructed with `eicrecon`. Signal
  hits are ~three orders of magnitude rarer than background.
- **Type / status.** Simulated structured event data (ROOT). Release status: internal to
  the ePIC collaboration; not publicly released.
- **Contacts.** nhanvtran (nhan.v.tran@gmail.com), per the corpus entry. **Confirm.**
- **Authorship & credit.** Not assigned; CRediT roles need the authors' input.
- **Sponsor / research organizations / facilities.** Not confirmed. **Flag as a gap.**
- **Sensitivity.** No PII or export-control indicators found; access is collaboration-gated.

## Accessibility

- **Policy.** Requires EIC/ePIC-collaboration Rucio credentials; not an open protocol.
- **Endpoints.** Rucio DIDs (retrieved via XRootD):
  `epic:/RECO/26.04.1/epic_craterlake/DIS/NC/10x100/minQ2=100/*` and
  `epic:/RECO/26.04.1/epic_craterlake/Bkg_Exact1S_2us/GoldCt/10um/DIS/NC/10x100/minQ2=100/*`.
  Tooling: `eic-shell`; https://eic.github.io/tutorial-file-access/01-introduction.html
- **Scale.** Ad hoc splits only: mixed 495 events (446 train / 49 test), signal-only 5,415
  events. ~5,700 hits/window, 15 features/hit (~342 KB/window at float32, an assumption).
  Campaign-wide size not stated. **Flag.**

## Interoperability

- **Structure.** `EDM4eic` on PODIO (Structure-of-Arrays, >1,000 branches); the benchmark
  uses a documented subset. Filtered per-hit schema in `data/SCHEMA.md`.
- **Provenance.** Geant4 full simulation with overlay merger, reconstructed by `eicrecon`.
  Truth chain: `TrackerHit → RawTrackerHit → RawHitAssociation → SimTrackerHit →
  MCParticle`. Signal membership must be inherited via `MCParticle.parents`;
  `generatorStatus` at face value mislabels secondaries (173 vs. correct 71 signal
  hits/event).
- **Dates.** Campaign April 2026; exact creation dates **not verified**.

## Reusability

- **License.** **Not stated in source material. Flag.** Do not assume open.
- **Versioning.** Campaign tag `26.04.1`. Earlier notes referenced `26.07.x`; the benchmark
  now pins April `26.04.1`.
- **Quality.** Truth labels come from simulation, so are exact up to the association rule
  above (highest-weight contributor for ~30% multi-contributor hits).
- **Splits.** Not frozen (`[GAP]` in `README.md` Section 2). Small (~2,470 target tracks in
  training), which the reference author calls the limiting factor.
- **Citation.** No formal citation. Cite the Indico category
  (https://indico.cern.ch/category/21857) until one exists.
- **Integrity & fixity.** No checksum manifest. **Flag.**

## Governed Use

Collaboration-gated access. Whether Genesis governed-use fields apply needs a human decision.

## AI Usability

- `training_use_status`: Yes (signal/background tagging). `evaluation_use_status`: Yes.
  `inference_use_status`: Conditional (input format is the same shape).
- Bounded: no augmentation allowed once splits are frozen.

---

**Gaps needing a live check or human decision:** dataset identifier (ARK/OSTI DOI), license,
contact confirmation, CRediT roles, sponsor/facility affiliations, creation dates, fixity
manifest, frozen splits, published extraction script, and open-access route.
