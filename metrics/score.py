"""Scoring for the EIC Streaming Tracking Benchmark.

Two families of metric, matching the benchmark's two coupled sub-tasks (see top-level
README.md Section 3):

1. Classification (per-hit / per-track signal-vs-background tagging) — `roc_auc` here is
   a direct adaptation of the classification primitive from benchmark-builder's
   `scripts/metrics.py`, vendored rather than imported so this repo has no external path
   dependency.

2. Track reconstruction (double majority, technical efficiency, fake rate) — genuinely
   bespoke to HEP tracking benchmarks; not implemented in `scripts/metrics.py`, which
   deliberately only covers the generic regression/classification motifs (see that
   script's own module docstring for why).

Neither family is "the" answer for every AI/ML motif — see references/ontology.md in the
benchmark-builder skill. These fit this benchmark specifically because its two sub-tasks
are, respectively, binary classification and track-level set matching.

Usage:
    from score import roc_auc, double_majority, technical_efficiency, fake_rate

    # classification
    auc = roc_auc(hit_truth_labels, hit_signal_scores)

    # tracking — each of predicted_tracks / target_tracks is a list of hit-index sets,
    # one list per event, aligned event-by-event
    dm = double_majority(predicted_tracks, target_tracks)
    eff = technical_efficiency(predicted_tracks, target_tracks)
    fr = fake_rate(predicted_tracks, target_tracks)
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Classification (per-hit / per-track signal tagging) — vendored from
# benchmark-builder/scripts/metrics.py's roc_auc, unchanged.
# ---------------------------------------------------------------------------


def roc_auc(y_true, y_score):
    """Area under the ROC curve via the rank-sum (Mann-Whitney U) formulation — exact,
    no thresholding loop, ties handled via average ranks. y_true must be binary (0/1)."""
    y_true = np.asarray(y_true, dtype=float)
    y_score = np.asarray(y_score, dtype=float)
    n_pos = np.sum(y_true == 1)
    n_neg = np.sum(y_true == 0)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(y_score, kind="mergesort")
    ranks = np.empty(len(y_score))
    # average-rank tie handling
    sorted_scores = y_score[order]
    i = 0
    rank = 1
    while i < len(sorted_scores):
        j = i
        while j + 1 < len(sorted_scores) and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        avg_rank = (rank + rank + (j - i)) / 2.0
        ranks[order[i : j + 1]] = avg_rank
        rank += j - i + 1
        i = j + 1
    sum_ranks_pos = np.sum(ranks[y_true == 1])
    auc = (sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


# ---------------------------------------------------------------------------
# Track reconstruction metrics — bespoke to this benchmark.
#
# Convention (fixed here, resolving the README's flagged >/>=  inconsistency between
# source slides): purity and completeness both use a strict ">" threshold of 0.5 for
# double majority; technical efficiency's per-particle "found" test uses ">=" 0.5,
# matching its own separate, looser definition. This is a deliberate, documented choice —
# see README.md Section 3, "Edge cases / definitions".
# ---------------------------------------------------------------------------

HitSet = frozenset


def _purity_completeness(predicted: HitSet, truth_hits_by_particle: dict) -> tuple[float, float, int | None]:
    """For one predicted track (a set of hit indices), find the truth particle that
    contributes the most hits to it, and return (purity, completeness, particle_id).
    particle_id is None if the predicted track is empty."""
    if not predicted:
        return 0.0, 0.0, None
    contributions: dict[int, int] = {}
    for particle_id, hits in truth_hits_by_particle.items():
        n = len(predicted & hits)
        if n:
            contributions[particle_id] = n
    if not contributions:
        return 0.0, 0.0, None
    best_particle = max(contributions, key=contributions.get)
    n_shared = contributions[best_particle]
    purity = n_shared / len(predicted)
    completeness = n_shared / len(truth_hits_by_particle[best_particle])
    return purity, completeness, best_particle


def double_majority(
    predicted_tracks: Sequence[Sequence[HitSet]],
    target_tracks: Sequence[dict],
) -> float:
    """Double Majority = (# predicted tracks with purity > 0.5 AND completeness > 0.5) /
    (# target tracks), summed across all events then divided.

    predicted_tracks: one list of hit-index sets per event.
    target_tracks: one {particle_id: hit_index_set} dict per event (the truth targets —
    see README.md's target definition: charged particles crossing >=3 layers, pT>=0.1 GeV,
    belonging to the signal event).
    """
    n_dm = 0
    n_targets = 0
    for preds, truth in zip(predicted_tracks, target_tracks):
        n_targets += len(truth)
        for track in preds:
            purity, completeness, _ = _purity_completeness(HitSet(track), truth)
            if purity > 0.5 and completeness > 0.5:
                n_dm += 1
    if n_targets == 0:
        return float("nan")
    return n_dm / n_targets


def technical_efficiency(
    predicted_tracks: Sequence[Sequence[HitSet]],
    target_tracks: Sequence[dict],
) -> float:
    """Technical efficiency = (# distinct target particles found by >=1 track of purity
    >= 0.5, deduplicated) / (# targets). Looser than double majority: ignores
    completeness, and a particle found by two different tracks counts once."""
    n_found = 0
    n_targets = 0
    for preds, truth in zip(predicted_tracks, target_tracks):
        n_targets += len(truth)
        found_particles = set()
        for track in preds:
            purity, _, particle_id = _purity_completeness(HitSet(track), truth)
            if particle_id is not None and purity >= 0.5:
                found_particles.add(particle_id)
        n_found += len(found_particles)
    if n_targets == 0:
        return float("nan")
    return n_found / n_targets


def fake_rate(
    predicted_tracks: Sequence[Sequence[HitSet]],
    target_tracks: Sequence[dict],
) -> float:
    """Fake rate = (# predicted tracks where no single truth particle owns a majority,
    i.e. purity <= 0.5) / (# predicted tracks emitted). Denominator is predicted tracks,
    NOT targets -- this metric does not complement double_majority/technical_efficiency."""
    n_fake = 0
    n_predicted = 0
    for preds, truth in zip(predicted_tracks, target_tracks):
        for track in preds:
            n_predicted += 1
            purity, _, _ = _purity_completeness(HitSet(track), truth)
            if purity <= 0.5:
                n_fake += 1
    if n_predicted == 0:
        return float("nan")
    return n_fake / n_predicted


def track_report(
    predicted_tracks: Sequence[Sequence[HitSet]],
    target_tracks: Sequence[dict],
) -> dict:
    """Convenience wrapper returning all three tracking metrics at once, matching the
    table format in README.md Section 3 / reference_solution/README.md."""
    return {
        "double_majority": double_majority(predicted_tracks, target_tracks),
        "technical_efficiency": technical_efficiency(predicted_tracks, target_tracks),
        "fake_rate": fake_rate(predicted_tracks, target_tracks),
    }
