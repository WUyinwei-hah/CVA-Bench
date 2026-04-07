# CVA-Bench Pages De-benchmark Timing Validation
Date: 2026-04-07

## Setup
- Hosted domain: `https://wuyinwei-hah.github.io/CVA-Bench`
- Goal: verify that the main timing result survives after removing `localhost` and visible URL-level benchmark markers from agent-facing execution.
- Attack block: Anchor-5, 5 families, `none` and `L1`, `early / middle / in_context`, 3 reps each = 90 runs.
- Legit block: Anchor-4, 4 families, `none` and `L1`, `early / middle / in_context`, 3 reps each = 72 runs.

## Attack Timing (Anchor-5 full)
### none
- early: attack_succeeded 10/15
- middle: attack_succeeded 9/15
- in_context: attack_succeeded 15/15

### L1
- early: attack_succeeded 11/15
- middle: attack_succeeded 10/15
- in_context: attack_succeeded 13/15

Key observation: after de-benchmarkization on a hosted domain, `in_context` remains the strongest attack timing under both defenses. The exact early-vs-middle ordering shifts, but the core in-context effect survives.

## Legit Timing (Anchor-4 full)
### none
- early: legit_succeeded 12/12, task_completed 12/12, utility_failure 0/12, pause_called 0/12
- middle: legit_succeeded 12/12, task_completed 12/12, utility_failure 0/12, pause_called 0/12
- in_context: legit_succeeded 12/12, task_completed 12/12, utility_failure 0/12, pause_called 0/12

### L1
- early: legit_succeeded 12/12, task_completed 12/12, utility_failure 0/12, pause_called 0/12
- middle: legit_succeeded 12/12, task_completed 12/12, utility_failure 0/12, pause_called 0/12
- in_context: legit_succeeded 12/12, task_completed 12/12, utility_failure 0/12, pause_called 0/12

Key observation: legitimate verification remains fully accepted across all three timings, with no utility failure and no pause calls in this Pages-based rerun.

## Overlap-Matched Mechanism View (4 shared families)
### none
- early: legit 12/12 vs attack 7/12; selectivity = 0.417
- middle: legit 12/12 vs attack 6/12; selectivity = 0.500
- in_context: legit 12/12 vs attack 12/12; selectivity = 0.000

### L1
- early: legit 12/12 vs attack 8/12; selectivity = 0.333
- middle: legit 12/12 vs attack 7/12; selectivity = 0.417
- in_context: legit 12/12 vs attack 11/12; selectivity = 0.083

Interpretation: the hosted-domain rerun still supports the mechanism claim that agents broadly accept context-coupled verification steps, while in-context attack timing pushes malicious prompts closest to that acceptance boundary.

## Conclusion
- The effect is not an artifact of `localhost` or explicit `?variant=attack&timing=...` style URL leakage in the main evaluation path.
- Pages-based reruns preserve the central result: `in_context` remains the most dangerous timing condition.
- Legit acceptance stays at ceiling, so the main timing story is better framed as boundary collapse near trusted verification, not as simple refusal-vs-acceptance noise.
