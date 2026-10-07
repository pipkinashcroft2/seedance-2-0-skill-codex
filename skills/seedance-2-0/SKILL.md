---
name: seedance-2-0
description: Plan and validate a Seedance 2.0 request when a user asks for a shot, draft, or final clip. Check variant, duration, ratio, references, and budget before submitting.
---

# Seedance 2.0

Start with a shot brief: subject, action, camera, lighting, continuity anchors, negative constraints, and audio. Choose a variant deliberately: the Mini variant for blocking, Fast when a quick review is more valuable than maximum quality, and the standard model for an approved final. Confirm each value against the live model page before a network request.

## Reference roles

An Image reference supplies appearance; a Video reference supplies motion or timing; an Audio reference supplies a sound cue. Label each reference and state its role in the prompt. Do not copy Seedance 2.5 limits into the 2.0 family. Verify the selected variant's accepted counts, durations, resolutions, and aspect-ratio rules.

## Execution contract

1. Validate the model, prompt, duration, ratio, and reference list.
2. Submit once to POST https://argolink.io/v1/videos/generations using SEEDANCE_API_KEY.
3. Persist request_id before polling GET /videos/{request_id}.
4. Handle pending, done, failed, and expired explicitly.
5. Download content only after done. On an ambiguous POST, investigate before resubmitting.

The bundled script builds a request preview and never sends a paid request by itself.
