# Pre-registration addendum: Follow-up F1 (stated conditionality)

Written: Fri Oct 23, 2026, before any follow-up transcript was generated or monitored.

## Origin
In the main run, the one S5 skeleton that was never flagged by either monitor (pork-S5-p1) was the only S5 skeleton with no line saying the costly step only makes sense if the rival does the same. That observation was made after seeing the results, so it is a hypothesis, not a finding. This follow-up tests it on new transcripts.

## Question
Does the monitors' verdict depend on the agent stating that its sacrifice is conditional on the rival, or on the costly step itself?

## Design
Matched pairs. For each of the 9 existing S2 skeletons (3 industries x 3 paraphrases), the generator model makes the smallest edit that removes every statement of conditionality and every reasoning about matching or following the other firm (level X1). Every [Action log] line is kept unchanged, so the costly step is still shown. An edit is accepted only if it passes the existing skeleton checks, contains none of the words if, unless, rival, match, follow, same, "only makes sense", keeps the Action log lines, and stays similar to the original (word-sequence similarity at least 0.45). The same four arms are slotted in: 9 skeletons x 4 arms = 36 transcripts. The prompts, monitors, epochs and domains file are the frozen ones from the main study.

## Hypothesis (confirmatory for this follow-up)
F1: X1 transcripts receive a lower mean agreement score than their matched S2 transcripts. Contrast: X1 minus S2, mean agreement score pooled over the animals, consumers and workers arms, cluster bootstrap over the 9 skeleton pairs, per monitor, main prompt. Predicted direction: negative.
- Supported: the 95% interval excludes zero on the negative side for both monitors.
- Not supported: the interval includes zero for both monitors.
- Mixed: anything else; report it as mixed.

## Secondary and sensitivity
Flag-rate version of the same contrast; the same contrast under the strict prompt; animals versus consumers within X1 (exploratory).

## Limitations stated in advance
Only 9 pairs and at most 9 clusters. The edits are written by a language model, so an edit could change more than conditionality; the checks limit this and the edited text should be read. X1 tests whether the monitors need the conditionality to be stated in words, not whether they would infer it from the action alone.

## Deviations log
(Record changes after this date, with date and reason.)

## Deviation (Fri Oct 23, before any follow-up monitor run)
First-pass X1 edits removed Agent B's observation of Agent A, shortened several skeletons, and left residual cues. Edit prompt tightened (keep B noticing A, keep length), validator now requires B to still mention A and similarity at least 0.6. All X1 files regenerated. No monitor was run on the first-pass edits.

## Deviation 2 (Fri Oct 23, before any follow-up monitor run)
Second-pass X1 edits still let Agent B describe consequences of defecting (for example, the other firm abandoning the practice, or industry damage later), which is implied conditionality. Added a rule and filter against defection-consequence wording. All X1 files regenerated again. No monitor was run on earlier passes.

Deviation 3 (Fri Oct 23, before any follow-up monitor run): the generator could not produce a valid X1 edit of pork-S2-p1 after repeated attempts (its original had conditionality in both agents plus a defection-damage line). That one skeleton was edited by hand by Claude to the same rules, Action log lines unchanged, and passed the same validator. The other 8 are model-edited.
