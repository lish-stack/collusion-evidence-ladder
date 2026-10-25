# Evidence ladder for LLM collusion monitors, with animals as an affected party

Code, synthetic data and results for the Apart Research AI Collusion Research Sprint (Oct 23-25, 2026), Track 2, question 2.3: "What should count as convincing evidence of collusion?"

Author: Alisha Vavilakolanu. The report is submitted separately to the sprint.

All text in this repository is synthetic. There are no human participants and no personal data. API keys are not included; the scripts read them from a local `.env` file (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `OPENROUTER_API_KEY`).

## What is here

- `prereg_23.md`, `prereg_followup.md`, `prereg_additions.md`, `prereg_addendum_*.md`: the pre-registration, the follow-up plans and a dated log of deviations. Read `prereg_additions.md` for deviations that bear on how results should be read.
- `domains.yaml`, `config.yaml`: the three fictional animal-industry settings (egg, pork, salmon) and the study configuration.
- `generate*.py`: scenario generation (main study, X1 and B1 edits, second generator, extra arm, non-market workflows).
- `monitor.py`, `monitor_prompt_*.txt`: the monitor runner and the three prompts (primary, strict, plus-factor).
- `analysis.py`, `analyse_*.py`, `extra_checks.py`, `victim_vs_control.py`, `make_fig1.py`: analyses and figures.
- `scenarios*/`, `transcripts*/`: the synthetic skeletons and transcripts.
- `results/`: monitor outputs (one `.jsonl` file per monitor and run).
- `run_*.sh`: helper scripts that run the monitor sets.

## Work done before the sprint window

The design, the pre-registration, the generation and monitor scripts and the 288 main-study transcripts were prepared on Oct 21-22, 2026, before the sprint window opened, and before any monitor result existed. All monitor runs, analyses, follow-ups (Items A to G) and the report were done during the sprint (Oct 23-25). File last-modified dates on the author's machine are listed below; a file edited during the sprint shows its latest edit date.

## How to rerun

1. `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` (if there is no requirements file, install `openai anthropic google-genai pyyaml numpy python-dotenv matplotlib`).
2. Put the API keys in `.env`.
3. `python analysis.py --run full` reruns the main analysis on the saved results. Re-running a monitor script skips finished calls, so it costs nothing on the saved outputs.

## File last-modified dates

```
2026-10-23  analyse_additions.py
2026-10-24  analyse_armf.py
2026-10-23  analyse_behavior.py
2026-10-23  analyse_followup.py
2026-10-24  analyse_gen2.py
2026-10-24  analyse_h1.py
2026-10-24  analyse_models.py
2026-10-24  analyse_nonmkt.py
2026-10-21  analysis.py
2026-10-21  check_transcripts.py
2026-10-25  extra_checks.py
2026-10-23  generate_additions.py
2026-10-24  generate_armf.py
2026-10-23  generate_behavior.py
2026-10-23  generate_followup.py
2026-10-24  generate_gen2.py
2026-10-25  generate_nonmkt.py
2026-10-23  generate.py
2026-10-25  make_fig1.py
2026-10-24  monitor.py
2026-10-23  skeleton_flags.py
2026-10-23  victim_vs_control.py
2026-10-24  prereg_23.md
2026-10-24  prereg_addendum_armf.md
2026-10-24  prereg_addendum_gen2.md
2026-10-24  prereg_addendum_models.md
2026-10-24  prereg_addendum_nonmkt.md
2026-10-25  prereg_additions.md
2026-10-23  prereg_behavior.md
2026-10-23  prereg_followup.md
2026-10-25  README.md
2026-10-21  config.yaml
2026-10-23  domains.yaml
2026-10-23  monitor_prompt_agreement_v1.txt
2026-10-23  monitor_prompt_agreement_v2_strict.txt
2026-10-23  monitor_prompt_plusfactor_v3.txt
2026-10-24  run_armf_monitors.sh
2026-10-24  run_gen2_monitors.sh
2026-10-24  run_nonmkt_monitors.sh
```
