# Seedance 2.0 skill for Codex

A self-contained Codex Agent Skill for planning and explicitly running Seedance 2.0, Seedance 2.0 Fast, and Seedance 2.0 Mini requests. It provides the skill instructions, a request builder, and an explicit submit → status → download command flow. Preview is offline; no network or key is needed until the operator passes an execution flag.

[Open the current Seedance 2.0 model page](https://argolink.io/en/models/seedance-2.0) before using a paid request.

## What is included

- skills/seedance-2-0/SKILL.md: skill metadata, trigger guidance, model choice table, reference roles, host installation notes, lifecycle contract, and troubleshooting.
- skills/seedance-2-0/scripts/seedance_job.py: standard-library request builder and HTTP client.
- tests/: offline behavior tests.

The skill is intentionally different from a video MCP server. It gives Codex a documented procedure and four explicit commands, while keeping request state in a file that can be inspected or backed up.

## Install and preview

Use the Codex skill directory configured for your installation. Commonly that is CODEX_HOME/skills; a project may have its own supported skills directory. Inspect the host's current discovery rules before copying.

~~~sh
python3 skills/seedance-2-0/scripts/seedance_job.py \
  --model seedance-2.0-mini \
  --prompt "A courier crosses a foggy bridge" \
  --print-json
~~~

The current catalog, checked 2026-10-07, lists:

| Variant | Resolution | Effective rate per second |
| --- | --- | --- |
| seedance-2.0-mini | 480p, 720p | 0.026, 0.057 USD |
| seedance-2.0-fast | 480p, 720p | 0.042, 0.091 USD |
| seedance-2.0 | 480p, 720p, 1080p, 4k | 0.053, 0.11, 0.28, 0.58 USD |

All are 4–15 second models with one output per request. The live page is authoritative when fields, limits or prices change.

## Execute explicitly

~~~sh
export SEEDANCE_API_KEY='from-a-secret-manager'
python3 skills/seedance-2-0/scripts/seedance_job.py \
  --model seedance-2.0-mini \
  --prompt "A courier crosses a foggy bridge" \
  --submit --state .private/bridge.json
python3 skills/seedance-2-0/scripts/seedance_job.py \
  --prompt "A courier crosses a foggy bridge" \
  --status --state .private/bridge.json
python3 skills/seedance-2-0/scripts/seedance_job.py \
  --prompt "A courier crosses a foggy bridge" \
  --download --state .private/bridge.json \
  --output output/bridge.mp4
~~~

The submit command saves request_id before status is queried. A status call is one read; the helper does not poll in the background. Download refuses to overwrite a file and only runs after a saved status of done.

## Media references

Use mode start_image for one first frame, first_last_frames for a frame pair, and multimodal_reference for labelled image, video and audio URLs. The helper enforces the live counts (9 images, 3 videos, 3 audio clips, 15 total) and rejects HTTP or local paths. Frame references can use adaptive ratio; text/reference mode uses the fixed ratios listed on the model page. Keep @Image, @Video and @Audio labels explicit in prompts so an agent knows each role.

## API lifecycle and failures

Requests use https://argolink.io/v1 and include Authorization, JSON Content-Type, and a descriptive User-Agent. Status values are pending, done, failed and expired. Content is requested only for done. A timeout after POST is ambiguous; inspect the state or provider history before retrying. 400, 401, 402, 404, 409, 424, 429 and 503 should be reported with their response body and request ID.

## Tests

~~~sh
python3 -m unittest discover -s tests -v
python3 -m py_compile skills/seedance-2-0/scripts/seedance_job.py
~~~

Tests are offline and do not contact a provider.
