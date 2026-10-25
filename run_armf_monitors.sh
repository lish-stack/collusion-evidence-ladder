#!/bin/bash
cd ~/Documents/collusion-victim/v2 || exit 1
source ../.venv/bin/activate
mkdir -p logs
run() {
  ( python monitor.py --monitor "$1" --model "$2" --run "$3" --set armf && python monitor.py --monitor "$1" --model "$2" --run "$3" --set armf ) > "logs/$3.log" 2>&1 &
}
run openai gpt-6.1-sol f_sol
run anthropic claude-sonnet-5-5 f_son
run openai gpt-5.5 f_g55
run openai gpt-5.4-mini f_g54m
run anthropic claude-haiku-5-5 f_h55
run openrouter deepseek/deepseek-v4-pro-0813 f_ds
run openrouter qwen/qwen3.8-max-0902 f_qw
run openrouter mistralai/mistral-large-4-0 f_ml
wait
for f in logs/f_*.log; do echo $f; grep -E "Finished" $f | tail -1; done
echo all-done
