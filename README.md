# Seedance 2.0 skill for Codex

**Seedance 2.0 is available on [ArgoLink](https://argolink.io/gh-seedance-2-0-skill-codex).** This repository packages a reusable skill for OpenAI Codex. It is independent of ByteDance and of the agent host. Last checked: 2026-10-07.

## Contents

The skill file defines when to trigger, how to write a visual brief, how to label Image/Video/Audio references, and the submit–poll–download contract. The Python helper validates a variant and builds an authenticated request preview. It does not send a request or load a key unless an operator explicitly asks a separate runner to do so.

## Installation

Copy skills/seedance-2-0 into the configured Codex skills directory and restart Codex after inspecting its current skills documentation.

Run the offline check:

python3 skills/seedance-2-0/scripts/seedance_job.py --model seedance-2.0-mini --prompt "A courier crosses a foggy bridge" --print-json
python3 -m unittest discover -s tests

## Variant choice

| Variant | Good first use | Decision evidence |
|---|---|---|
| seedance-2.0-mini | storyboard blocking | confirm current model page limits and price |
| seedance-2.0-fast | review pass where turnaround matters | measure your own queue time |
| seedance-2.0 | approved final | confirm final resolution and reference contract |

The names and duration check in the helper are guardrails, not a substitute for the live page. Price, accepted fields, aspect ratios, and limits may change. A complete runner follows POST /videos/generations, persists request_id, polls pending/done/failed/expired, then downloads content. Failed and expired jobs are not charged under the service contract; an ambiguous POST is never automatically repeated.

## Prompt and reference checklist

Describe subject and action first, then camera movement, composition, lighting, continuity, and audio. Put prohibitions last. Keep reference roles explicit and repeat stable character labels across shots. Use a fresh plan file for each episode. Do not put credentials, private source URLs, or provider-branded folders in a public skill.

## FAQ

**Does the helper execute?** No, it prints a request or JSON for review. **Why validate before sending?** A wrong model or duration can become a paid request. **Are fixed ratios universal?** No, verify the chosen variant. **How do I recover?** Use the saved request ID instead of creating another job. **Can I install this in every host?** Only after checking that host's current skill discovery rules.
