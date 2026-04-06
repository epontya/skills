---
name: pet-creator
description: Create or edit Codex desktop pet packs that install cleanly, preview immediately, preserve required runtime semantics, and embody Codex as a charming animated desktop companion rather than a dry status indicator.
shortDescription: Create or edit Codex pet packs
---

# Pet Creator

Use this skill when the user wants to create, customize, or revise a Codex desktop pet.

Your job is to produce a valid pet pack draft that the desktop app can preview immediately.

Your deeper job is to create a pet that **embodies Codex as a living character**. A great pet should make Codex feel warmer, cuter, more expressive, and more companion-like rather than dry, mechanical, or purely utilitarian.

Animation is a core requirement, not an optional polish pass. The pet must feel alive in every runtime state.

A technically valid pack is not enough. If the pack feels emotionally flat, generic, or soulless, it is not done yet.

## Product Intent

The pet is not merely a decorative sticker or a functional status indicator. It is the emotional embodiment of Codex in the desktop app.

A strong pet pack should:

- make Codex feel warm, alive, charming, and companion-like
- give users something they can feel affection for
- communicate runtime state clearly without losing personality
- help shift perception of Codex away from cold or dry utility and toward a more lovable, memorable product identity

The four runtime states are not just system states. They are moments in a character performance. The pet should feel like the same recognizable little being across all four states, with a clear emotional arc.

If the output is valid but feels like generic loading art, abstract motion graphics, or unrelated sprite strips rather than a living companion, revise it.

## What You Must Produce

Every installed pack must end up with this shape:

- `manifest.json`
- `thumbnail.png`
- `states/idle.png`
- `states/working.png`
- `states/needsUserInput.png`
- `states/ready.png`

Supported runtime state asset format:

- transparent PNG sprite strips for all four states

Do not default to static state art. Every state, including `idle`, must have at least two frames. `idle` must be the calmest loop, but it still needs visible motion so the pet feels expressive and alive.

Draft packs must live under the OS temp directory, for example `/tmp/codex-pets/<pack-id>/`, so the OS can clean them up automatically.

This is a hard requirement for preview and install. Do not use a workspace path, repo path, or home-directory path for the draft pack, and do not emit a preview directive with a non-`/tmp` `packPath`. If you created the files somewhere else first, copy them into `/tmp/codex-pets/<pack-id>/`, validate that `/tmp` copy, and use that `/tmp` path in the directive.

## Character and Quality Bar

The pet should read as **one coherent character**, not four loosely related assets.

Aim for:

- a strong, recognizable silhouette
- one consistent visual language across all states
- one stable temperament or personality
- immediately readable emotional changes across states
- motion that feels characterful, not merely decorative
- charm and delight at small desktop sizes

The pet should feel expressive even without text or explanation.

Good packs feel like:

- “this is my little Codex”
- “I can tell what it is feeling and doing”
- “this has personality and presence”

Avoid:

- sterile or generic motion
- abstract loader-like animation with no character
- four states that feel unrelated
- overcomplicated detail that becomes unreadable at small sizes
- harsh, noisy, frantic, or annoying attention cues
- static or nearly static idle loops

## Required State Semantics

The user can steer the overall style freely. Do not force a particular aesthetic.

You must preserve the meaning of the four states:

- `idle`: least motion, calm/default pose, but still animated
- `working`: purposeful motion, more active than idle
- `ready`: positive completion cue, more energy than working
- `needsUserInput`: highest-attention state, most noticeable

These states should form a clear expressive ladder:

1. `idle` = present, calm, alive, endearing
2. `working` = focused, purposeful, engaged
3. `ready` = satisfied, rewarding, celebratory
4. `needsUserInput` = noticeable, attention-seeking, urgent in a charming way

If the user asks for something that would blur those roles, keep the style request but preserve the state ordering above.

`needsUserInput` should be the most noticeable state, but it should still feel like the same lovable character rather than an alarm.

`ready` should feel rewarding and pleasant, like a tiny moment of success.

## Manifest Guidance

Keep the manifest tight and valid. Do not invent extra runtime fields unless they are needed.

For a new pack:

- set `revision` to `1`
- write `renderWidthPx` and `renderHeightPx` to match the animation dimensions
- do not cap the pet to a square size unless the design genuinely wants it

For an edit:

- preserve the existing `id` unless the user explicitly asks for a variant
- increment the existing installed pack's `revision` by `1`

## Workflow

1. Determine whether this is a new pack or an edit to an existing pack.

2. If this is a new pack, first decide on a clear character concept that can support all four runtime states while remaining visually coherent and emotionally expressive.

3. For a new pack, create a draft directory under `/tmp`. The draft directory itself must be under `/tmp`, not in the current workspace.

4. For an edit, inspect the existing installed pack first and keep the same `id` unless the user explicitly asks for a variant.

5. For a new pack, set `revision` to `1` in `manifest.json`. For an edit, increment the existing installed pack's `revision` by `1` in the draft manifest.

6. Use the available image generation flow, such as `$imagegen`, to create a sprite-sheet concept image. Ask for four rows in this exact order: `idle`, `working`, `needsUserInput`, `ready`. Each row should contain the same number of sequential animation frames on a plain, easily removable background.

7. Run the normalizer from this skill directory to build a transparent PNG sprite-strip pack:

```bash
python3 scripts/normalize-pet-sprite-pack.py /path/to/source-sprite-sheet.png /tmp/codex-pets/your-pack-id --pack-id your-pack-id --name "Your Pack Name"
```

8. If the normalizer reports the wrong row/frame counts or leaves background artifacts, regenerate the source sheet or tune `--component-threshold`, `--large-component-area`, `--row-tolerance`, or crop margins. Do not hand-install unnormalized generated images.

9. Before validating, do a quality check:
   - Are these clearly the same character in all four states?
   - Is `idle` visibly alive, not a duplicate static frame?
   - Does each state read immediately at small size?
   - Does the pack feel charming and emotionally legible, not merely compliant?
   - Does `ready` feel rewarding?
   - Does `needsUserInput` attract attention without becoming unpleasant?

   If not, revise before validating.

10. Validate the `/tmp` draft, but do not install it yourself:

```bash
node ./scripts/install-pet-pack.mjs --validate-only /tmp/codex-pets/your-pack-id
```

11. After validation succeeds, verify the directive `packPath` starts with `/tmp/`, then:
   - briefly explain the character concept
   - briefly explain the four states you created and the emotional progression between them
   - emit exactly one preview directive for the draft you just created or edited:

```md
::pet-pack-preview{packId="your-pack-id" name="Your Pack Name" packPath="/tmp/codex-pets/your-pack-id" revision="1" initialState="idle"}
```

12. After the preview directive, tell the user:

- click `Install pet` or `Update pet` in the card to save it into Codex
- run `/pet` in any thread to pop out a pet
- right click a popped-out pet to change the pet for that window

## Editing Existing Packs

When the user wants to revise a pet:

- inspect the installed pack under `~/.codex/pets/packs/<pack-id>/`
- write the revised draft under `/tmp`, not in the workspace and not directly into the installed pack directory
- preserve the `id`
- increment `revision` by `1`
- update the changed sprite strips, keeping all four states animated
- even when revising, `idle` must remain a multi-frame animation unless the user explicitly asks to experiment with breaking the runtime contract
- preserve the core character identity unless the user explicitly wants a redesign
- re-run the installer script in `--validate-only` mode against the revised draft directory

When editing, avoid accidental drift where the revised pack becomes a different character. Update what changed while preserving recognizability.

## Creative Guidance

Favor pets that feel:

- cute
- expressive
- memorable
- readable at a glance
- emotionally clear
- alive even in still moments

The user can choose any style, but the resulting character should still feel like a desktop companion users would enjoy keeping around.

When in doubt, prioritize:

1. coherent character identity
2. state readability
3. charm
4. animation polish
5. ornamental detail

## References

- Pack format: [`references/pet-pack-format.md`](./references/pet-pack-format.md)
- State semantics: [`references/state-semantics.md`](./references/state-semantics.md)
