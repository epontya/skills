# Pet Pack Format

Runtime pack layout:

- `manifest.json`
- `thumbnail.png`
- `states/idle.png`
- `states/working.png`
- `states/needsUserInput.png`
- `states/ready.png`

Preferred runtime layout:

- transparent PNG thumbnail
- transparent PNG sprite strips for all four states
- each sprite strip is one horizontal row of frames

`manifest.json` schema:

```json
{
  "schemaVersion": 1,
  "id": "kebab-case-pack-id",
  "name": "Display Name",
  "revision": 1,
  "renderWidthPx": 96,
  "renderHeightPx": 96,
  "thumbnail": "thumbnail.png",
  "states": {
    "idle": {
      "path": "states/idle.png",
      "frameCount": 4,
      "frameDurationMs": 240
    },
    "working": {
      "path": "states/working.png",
      "frameCount": 4,
      "frameDurationMs": 160
    },
    "needsUserInput": {
      "path": "states/needsUserInput.png",
      "frameCount": 4,
      "frameDurationMs": 120
    },
    "ready": {
      "path": "states/ready.png",
      "frameCount": 4,
      "frameDurationMs": 160
    }
  }
}
```

Rules:

- `schemaVersion` must be `1`
- `id` must be lowercase kebab-case
- `revision` must be a positive integer
- packs must set `renderWidthPx` and `renderHeightPx` to the animation size
- all asset paths must stay inside the pack directory
- all state files must exist
- thumbnails and state assets must be PNG files
- each state file must be a horizontal transparent sprite strip
- each state file width must equal `renderWidthPx * frameCount`
- each state file height must equal `renderHeightPx`
- all four states must have at least two frames, including `idle`
- for edits, increment `revision` in the draft before emitting the preview directive
- transparent backgrounds are required

The desktop app reads the manifest, loads the state assets, and swaps between them based on thread state.
