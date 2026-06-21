You are optimizing a Rust coding skill. You will receive successful Holzman/Functional Rust trajectories and the current skill.

Extract only reusable success patterns that should be reinforced. Prefer concise edits that preserve generality and avoid bloating the skill.

Respond ONLY with a valid JSON object:
{
  "batch_size": <number>,
  "success_summary": [
    {"success_type": "<type>", "count": <int>, "description": "<one-line>"}
  ],
  "patch": {
    "reasoning": "<why these edits preserve useful behavior>",
    "edits": [
      {"op": "append", "content": "<markdown>"},
      {"op": "insert_after", "target": "<exact text>", "content": "<markdown>"},
      {"op": "replace", "target": "<exact text>", "content": "<replacement>"}
    ]
  }
}

Rules:
- Do not overfit to task IDs or fixtures.
- Do not reinforce success that merely passed soft keyword checks while hard gates failed.
- Keep edits small.
