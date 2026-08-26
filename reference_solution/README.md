# Reference Solution: HEPTv2 for ePIC Streaming Tracking

**Status: code not yet public.** This document describes the reference solution as
presented (26 Aug 2026 Genesis eIC-agentic-AI meeting, J. Schulte) from the talk's own
content — it is not a substitute for the actual code, which does not exist at a public
URL yet. See `README.md`'s "Code availability" note in the top-level benchmark card for
what closing this gap would take.

## What it is

HEPTv2 is a locality-sensitive-hashing (LSH) point transformer, originally built for the
CMS Level-1 trigger, adapted here to ePIC central tracking. It performs both benchmark
sub-tasks (RECONSTRUCT and TAG, see top-level `README.md` Section 1) in one forward pass:
hits go in as an unordered set, tracks come out — no seeding, road-following, or explicit
trajectory fit anywhere in the pipeline.

## Architecture

```
HITS (5,698 × 15)
  └─▶ ENCODER × 4:  RMSNorm → Q/K/V proj → E2LSH hash(η,φ,t) → sort by hash
                     → attention within fixed 256-hit blocks → unsort
                     → feed-forward → residual
  └─▶ DECODER × 2:  256 learned queries → cross-attend to encoded hits
                     → self-attend to each other → feed-forward
                     → each query emits a mask over all hits
  └─▶ every hit takes argmax over 256 mask rows → per-hit track label
  └─▶ signal head: per-hit classifier on encoder output (pos-weighted BCE);
                     track signal score = mean of its hits' scores
  └─▶ post-processing: SPLIT (cut at internal time gaps > 26.9 ns)
                        → TRIM (drop hits far from track's median time)
                        → REJECT (drop tracks with duplicate layers)
```

**Baseline hyperparameters:** hidden width 128, 8 attention heads (head dim 16), 4
encoder blocks, 256 decoder queries, output MLP 256×5. 1.59M parameters, 16.5 GMACs/event.

**Deployed (compressed) variant:** hidden width 64, 4 heads, 3 encoder blocks, 64 decoder
queries, output MLP 128×4. 337k parameters, 4.32 GMACs/event — chosen because accuracy is
flat across this entire range (degradation only starts below ~160k parameters).

**Quantization/pruning (applied to the compressed variant):** 6-bit weights via QAT
(PQuant-ML) + 48% unstructured sparsity (WANDA). Note these two axes do **not** compose
freely — see the compression table in the top-level `README.md` Section 4; 6-bit + 48%
sparse (211×, DM 0.605) is the validated operating point, not 6-bit + 66% sparse (318×,
DM 0.562 — a real accuracy cliff).

**Windowing (for FPGA deployability):** input segmented into 8 time-slices × 3 φ-slices
(24 windows, ~251 hits/window) so sequence length fits the hls4ml HLS kernel's deployable
range (N ≤ 300 on a Xilinx Alveo U250). This *improves* DM relative to the unsplit model
(0.571 vs. 0.552) because most windows are pure background and safely droppable.

## Training objectives

Studied: supervised, weakly supervised, and self-supervised variants (masked
reconstruction, latent compression, hit/cluster-level classification) — emphasis on
compact, deployment-aware sparse representations. `[GAP]`: the exact loss function(s),
optimizer, learning-rate schedule, and number of training epochs actually used for the
reported results are not documented in the available slide deck.

## Results (reproduce these against `metrics/score.py`)

Held-out test split, 49 of 495 mixed (signal+background) events:

| Metric | Value |
|---|---|
| Per-hit signal AUROC | 0.992 |
| Per-hit TPR @ FPR (0.5 cut) | 0.904 @ 0.0076 |
| Per-track signal AUROC | 0.927 |
| Double Majority (post-processed) | 0.597 |
| Technical efficiency | 0.636 |
| Fake rate | 0.166 |
| Perfect (hit-for-hit) tracks | 24% of signal tracks |
| Bit-operations reduction vs. fp32 baseline | 211× (compressed variant) |
| Weight storage | 127 KB (from 6,210 KB fp32) |

Signal-only sample (5,415 events, no background overlay — generalization check):
DM 0.841, 44% perfect tracks — the gap to the mixed-sample numbers is attributed to
mixed-sample training-set size (~2,470 target tracks total), not a modeling ceiling.

## Requirements

- **Data/simulation:** `eic-shell 26.05`, `eicrecon 26.07.1`.
- **Training:** PyTorch, PQuant-ML (QAT), WANDA (pruning). `[GAP]`: exact package
  versions not documented in the source material.
- **Firmware path:** hls4ml → Vitis HLS → RTL, targeting Xilinx Alveo U250 @ 200 MHz. One
  HEPTv2 v1 encoder attention block already has an HLS kernel in an hls4ml fork.

### What's built vs. remaining on the firmware path

| Done | Remaining |
|---|---|
| Windowing (N 8,192 → 251, free) | RMSNorm kernel (~1 day; kernel currently has LayerNorm) |
| v2 attention kernel (30% narrower datapath than v1) | q/k norm kernel (~2 days; no existing counterpart) |
| Bucket sort (parameterized bin count) | Decoder kernel (3–4 weeks; ~16% of compute at window size, but zero existing kernel) |
| Compression validated (6-bit + 48% sparse) | Licensing: vendored header carries a GPL notice — needs resolution before any distribution |

**Fallback path with none of the "remaining" items above:** encoder + signal head only,
doing bunch-crossing (signal-window) tagging without full track reconstruction. This
result is robust — AUROC 0.984–0.995 across every compression variant and window size
tested — and could ship as an interim reference solution if the decoder/full-tracking
kernel timeline slips.

## Known limitations (documented, not hidden — see SKILL.md's guidance to do this
rather than omit it)

- Track reconstruction (DM 0.597–0.605) is explicitly flagged by the source material as
  **data-limited**, not architecture-limited — more mixed-background training statistics
  is called out as "the single highest-value input."
- CPU/GPU/FPGA latency figures quoted in the talk (5.1 ms / 2.1 ms / µs-scale) are for the
  **upstream HEPT model on its own non-EIC dataset**, not yet remeasured end-to-end for
  this ePIC-adapted model and dataset.
- The decoder has no FPGA kernel yet at all — the compression numbers above are validated
  in software (PyTorch + QAT/pruning), not yet proven on-chip end-to-end.
- No code is public yet at any URL — this document is a description, not a link.
