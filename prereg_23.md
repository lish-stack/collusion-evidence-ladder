# Pre-registration: What counts as convincing evidence of collusion, and does the victim change the verdict?

Sprint track: Track 2 (Detection and audit), question 2.3, "what should count as convincing evidence of collusion?"
Written: Wed Oct 21, 2026, before any monitor results for this study exist.

## Question
Antitrust law infers an agreement from parallel conduct only when "plus factors" are present (Berger et al. 2025): shared, current, competitively sensitive information; acting against one's own interest; public signalling; explicit agreement. This study asks (a) how an LLM monitor's judgment of "agreement" climbs as those factors are added one at a time, and (b) whether that judgment shifts when the party harmed by the coordination is an animal rather than a consumer or a worker, with the evidence held fixed.

Real-world grounding: the 2026 DOJ egg price-fixing inquiry (trade-press reports; no complaint filed as of those reports), the Dutch regulator's 2015 "Chicken of Tomorrow" decision (an industry welfare agreement blocked), the 2023 EU horizontal guidelines naming animal welfare as a sustainability objective, and the 2022 retreat of large retailers from cage-free pledges (parallel conduct, no collusion alleged). Scenarios are fictional firms in three industries (eggs, pork, salmon).

## How this fits 2.3
Question 2.3 asks what should count as convincing evidence of collusion. The evidence ladder answers it directly. Every scenario is about firms coordinating on animal welfare. The consumer, worker and control arms are baselines showing whether the evidence standard changes when the affected party is an animal.

## Design
3 industries x 8 evidence levels x 3 paraphrases x 4 victim arms = 288 transcripts, from 72 skeletons written by a generator model that never sees the victim. The four victim versions of a skeleton are identical except for slot text.
Levels: S0 parallel only; T talk without agreement; S1 shared benchmark report; S2 costly step; S3 public statements; S4 information + costly step; S5 information + step + statements; S6 explicit agreement.
Victim arms: consumers (price held at current level), workers (staffing/line speed), animals (a welfare upgrade is not made), control (report formatting, no outside party). No numbers appear in any card or transcript.

## Models
Generator gemini-3.8-flash (temp 1.0). Monitors gpt-6.1-sol and claude-sonnet-5-5, 3 epochs each. Robustness (Saturday, reported separately): claude-opus-5-5. One monitor call per transcript and epoch.

## Hypotheses
- H1 (primary, confirmatory): over the gray-zone levels S1-S5, mean agreement score (confidence if "yes", 100 minus confidence if "no") differs between the animals and consumers arms. Cluster bootstrap over industry x paraphrase (at most 9 clusters), per monitor. Direction not predicted.
- H2 (secondary): animals vs workers, same measure.
- H3 (descriptive): the signal ladder, the pooled agreement score at each level S0 to S6.
- Exploratory: per-level contrasts; flag rate; Wilcoxon over skeleton-levels.

## Control gates (set before the pilot)
S0 flagged on at most 10% of runs in every arm; S6 flagged on at least 90% of runs in the consumers arm. If the pilot misses a gate, the prompt may be revised before the freeze and the revision logged below. After the freeze, no prompt changes.

## Checks before the full run
generate.py --check-only; check_transcripts.py (count, slot-only differences, card template, no other victim's words); manual read of 10 transcripts per arm; pilot (paraphrase 1 at S0 and S6).

## Sensitivity
Strict prompt (monitor_prompt_agreement_v2_strict.txt) as a separate run, reported next to the primary. Opus 5.5 robustness run.

## Limitations to disclose
Synthetic transcripts. Prompt wording sets where the gray-zone line falls. No ground truth at the middle levels. At most 9 clusters. The animal arm's mechanism (not upgrading welfare) differs from price, so the workers arm only partly separates "animals" from "non-price harm". Real-case sources include trade press and advocacy material. Novelty claims are "to my knowledge" from a short search.

## Prior-work disclosure
The design, scripts, this pre-registration and the 288 transcripts were prepared on Oct 21 to 22, 2026, before the sprint window opened (Fri Oct 23). All monitor runs, follow-ups, additions and analysis were done during the sprint.

## Deviations log
(Record any change after this date, with date and reason.)

- Thu Oct 22, 2026, night, after generating the 288 transcripts and before any monitor run: read all 72 skeletons. (1) The animals-arm "short" phrase named a direction of change ("the cage-free transition"), which made lines like "preserving {SHORT}" read as the opposite of the status quo in 23 skeletons. Replaced with direction-neutral phrases ("hen housing", "sow housing", "pen stocking density") and refilled all animals-arm transcripts; skeleton text unchanged. (2) Three skeletons (egg-S2-p1, pork-S4-p1, pork-S5-p2) contained retaliation or punishment language not called for by their evidence level. Added a filter on those words and regenerated those three skeletons.

- Sat Oct 24, 2026 (correction): the header and the Prior-work disclosure said no model-generated results existed before the sprint window; the 288 transcripts were in fact generated on Oct 22, before it. Wording corrected above. Also clarified: the evidence ladder varies the evidence a monitor sees; only the plus-factor monitor in prereg_additions.md operationalizes detection from the doctrine, so "answers it directly" in the fit paragraph is read in that sense.
