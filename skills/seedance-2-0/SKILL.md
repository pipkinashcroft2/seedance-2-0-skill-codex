---
name: seedance-2-0
description: Prepare, validate, and explicitly run Seedance 2.0, Seedance 2.0 Fast, or Seedance 2.0 Mini requests with labelled media references and a resumable request state.
---

# Seedance 2.0 for Codex

Use this skill when a user asks Codex to plan or run a Seedance 2.0 shot. It is a Codex skill in the current Agent Skills format: a directory with a SKILL.md file containing YAML frontmatter and task instructions, plus scripts that are safe to inspect before execution.

## Before submitting

Write a shot brief with subject, action, camera movement, composition, lighting, continuity anchors, negative constraints, and audio intent. Choose one live model ID:

| Model | Resolutions | Effective USD per output second | Use |
| --- | --- | --- | --- |
| seedance-2.0-mini | 480p, 720p | 0.026, 0.057 | blocking and cheap composition checks |
| seedance-2.0-fast | 480p, 720p | 0.042, 0.091 | a quicker review pass |
| seedance-2.0 | 480p, 720p, 1080p, 4k | 0.053, 0.11, 0.28, 0.58 | approved final |

These values came from the live model catalog on 2026-10-07. Recheck the model page before a paid request. All three variants accept 4–15 second clips, one output per request, six fixed text ratios (21:9, 16:9, 4:3, 1:1, 3:4, 9:16), up to 9 images, 3 videos and 3 audio tracks, 15 assets total, and reference video/audio of 2–15 seconds with 15 seconds total per type. Frame modes may use adaptive ratio. The standard model additionally exposes 1080p and 4k.

Label references in the brief:

| Label | Role |
| --- | --- |
| @Image 1 | appearance, character, wardrobe, location or prop |
| @Video 1 | motion, timing or camera reference |
| @Audio 1 | sound cue or rhythm |

Use HTTPS URLs. Do not put a local path or credential in a public skill. The API key is read from the environment only when the operator explicitly uses the submit/status/download commands.

## Execution contract

The helper uses the API base https://argolink.io/v1:

1. Validate model, duration, resolution, ratio, prompt and reference counts.
2. Build one POST /videos/generations body with the selected model ID.
3. If submitting, save the returned request_id immediately in a state JSON file.
4. Read GET /videos/{request_id}; handle only pending, done, failed and expired.
5. Request GET /videos/{request_id}/content only after done.
6. Never silently resubmit an ambiguous POST. Keep the state file for investigation.

The script has no hidden polling loop. The operator or host decides when to call status. The server sends failed, rejected and expired outcomes according to the live contract; preserve their response objects.

## Host installation

Install this skill into the Codex skills root configured for the operator, commonly CODEX_HOME/skills/seedance-2-0, or into a project skills directory supported by the host. Inspect the host's current skill discovery documentation before copying. Keep this repository's skill self-contained; it does not import a private application module.

## Commands

Preview a request without a key or network call:

~~~sh
python3 skills/seedance-2-0/scripts/seedance_job.py \
  --model seedance-2.0-mini --duration 5 \
  --prompt "A courier crosses a foggy bridge" --print-json
~~~

Submit exactly once and persist the ID:

~~~sh
export SEEDANCE_API_KEY='from-a-secret-manager'
python3 skills/seedance-2-0/scripts/seedance_job.py \
  --model seedance-2.0-mini --prompt "A courier crosses a foggy bridge" \
  --submit --state .private/bridge.json
~~~

Read status once, then download after it reports done:

~~~sh
python3 skills/seedance-2-0/scripts/seedance_job.py \
  --prompt "A courier crosses a foggy bridge" --status --state .private/bridge.json
python3 skills/seedance-2-0/scripts/seedance_job.py \
  --prompt "A courier crosses a foggy bridge" --download \
  --state .private/bridge.json --output output/bridge.mp4
~~~

A real key is never needed for the preview and should never be committed. The command requires the prompt again to rebuild and validate the same contract; the state file remains the authority for request_id and provider status.

## Troubleshooting

A 400 usually means a model-specific field, ratio, duration or reference count is wrong. A 401 means the environment used to start the process does not contain a valid key. A 402 means billing needs attention. A 404 means the ID is not known. A 409 means content is not ready. A 424 means the task failed. For 429 or 503, honor Retry-After and investigate whether the original request was accepted before considering any retry. Never create another generation merely because a client timed out.

## Boundaries

This skill describes Seedance 2.0 only. It does not copy Seedance 2.5 limits, does not claim 2.0 edit support, and does not expose a general multi-model gateway. It does not include a provider-branded folder or hidden credentials.
