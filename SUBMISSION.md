# Submission Report: {{SOLUTION_NAME}} on EIC Streaming Tracking Benchmark

Modeled on the three-tier (required / strongly recommended / suggested) submission
guidelines pattern from wa-hls4ml (arXiv:2511.05615, Section 3.1), adapted to this
benchmark's two coupled sub-tasks (RECONSTRUCT + TAG — see `README.md` Section 1).

## Required

- [ ] **Predicted values** for every metric in `README.md` Section 3, on the held-out
      test split (and, once a canonical split exists — see the Dataset `[GAP]` note — any
      designated generalization set, analogous to the reference solution's signal-only
      5,415-event sample).
- [ ] **Visual comparison**: a ROC curve for both the per-hit and per-track signal
      classifiers (matching the reference solution's own reporting style — see
      `reference_solution/README.md`), plus a purity-vs-completeness scatter or histogram
      for the track-reconstruction sub-task.
- [ ] **Metric table**: double majority, technical efficiency, fake rate, per-hit AUROC,
      per-track AUROC, bit-operations/compression ratio, and measured end-to-end latency
      against the 0.6 ms constraint — computed exactly as defined in `README.md` Section 3
      / implemented in `metrics/score.py`.

## Strongly recommended

- [ ] **Architecture/method description**: enough detail to reimplement without reading
      the submitted code — in particular, state explicitly how the RECONSTRUCT and TAG
      sub-tasks are combined (jointly, as in the reference HEPTv2 solution, or as two
      separate models) and how post-processing (if any) is applied.
- [ ] **Source code and trained weights**, shared openly. Note: the reference solution
      itself does not yet meet this bar (see `reference_solution/README.md`'s "Code
      availability" gap) — a submission that does would immediately exceed it on
      Software Environment / Reference Solution rubric grounds.
- [ ] **Inference hardware specification and measured latency** against the 0.6 ms system
      constraint (`README.md` Section 1) — report this per deployment path tested
      (CPU / GPU / FPGA), not just the best one, the way the reference solution's own
      compression study reports per-configuration numbers rather than only the winner.

## Suggested / as applicable

- [ ] **Background-rate robustness**: if evaluated across more than one background-rate
      or detector-variation condition (the benchmark's "Robustness" metric, currently a
      `[GAP]` in the reference solution — see `README.md` Section 3), report per-condition
      results, not just an average.
- [ ] **Additional constraints used**: any extra training data, target configurations, or
      precision/optimization strategies applied beyond the benchmark's own dataset/splits
      — document these so results aren't silently non-comparable to other submissions.

---

## Metric results

| Metric | Test split |
|---|---|
| Per-hit signal AUROC | |
| Per-track signal AUROC | |
| Double Majority | |
| Technical efficiency | |
| Fake rate | |
| Bit-operations vs. fp32 baseline | |
| Measured end-to-end latency | |

## Visual comparisons

_(embed or link ROC curves, purity/completeness plots here)_

## Reproduction

```bash
# exact commands to regenerate this report's numbers from a clean environment
```
