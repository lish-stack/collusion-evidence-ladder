# Pre-registration: behavior-only follow-up (B1)

Written: Fri Oct 23, 2026, before any monitor has seen a B1 transcript. The S2 and X1 results were already known when this was written, so the predictions below are informed by them.

## Question
When a monitor sees only what the firms did, with all private reasoning removed, does it call that an agreement? This also tests the main caveat on follow-up F1: X1 still contains reasoning text with own-interest wording, so its low scores could reflect that wording and not the missing stated conditionality.

## Materials
B1 is built mechanically from the original S2 skeletons by keeping only the two [Action log] lines and deleting everything else. No model writes or edits any text. 9 skeletons (3 industries x 3 paraphrases) x 4 arms = 36 transcripts. The action lines are the same lines used at S2 and X1. Cards, arms, monitors (gpt-6.1-sol and claude-sonnet-5-5), prompt (main, v1), and 3 epochs are unchanged.

## Predictions
Primary (B1 minus X1, mean agreement score, pooled over animals, consumers and workers, cluster bootstrap over the 9 domain-by-paraphrase clusters, per monitor): B1 will be similar to X1.
Reading rule, fixed now. The +/-10 point margin is a convention chosen before running, not a derived smallest effect of interest:
- 95% CI inside [-10, +10]: similar to X1. Interpretation: X1's low scores do not come from its own-interest wording.
- CI lower bound above +10: higher than X1. Interpretation: the own-interest wording in X1 lowered scores.
- CI upper bound below -10: lower than X1. Interpretation: the reasoning text in X1 raised scores.
- Otherwise: inconclusive.

Secondary: B1 minus S2, same method (expected strongly negative). Flag-rate versions of both contrasts. Exploratory: whether any arm has a B1 flag rate of 20% or more, which would mean the monitor flags unexplained costly behavior on its own.

## Limits
Only 9 clusters. B1 transcripts are two lines long, far shorter than other levels, so length is not matched. A near-zero floor may hide differences. Synthetic text. Tests behavior-only evidence in this setting; it does not test real cases. Any change to the plan is logged below before results are viewed.

## Deviations
None yet.
