# State Semantics

Keep the overall character style consistent across all four states. Change pose, expression, or motion intensity, not the identity of the character.

State expectations:

- `idle`
  - calm default pose
  - least visual noise
  - smallest loop
  - must still be animated; never ship idle as a one-frame sticker
  - if idle frames are duplicates or effectively static, the draft is not acceptable
- `working`
  - purposeful motion
  - visibly active but not frantic
  - should read as "busy"
- `ready`
  - clear success/completion cue
  - more energy than working
  - should read as "done"
- `needsUserInput`
  - highest attention state
  - strongest pose or motion
  - should read as "look at me"

When revising a pack, do not let `idle` become louder than `working`, and do not let `needsUserInput` become subtler than `ready`.

The relative motion ordering matters:

- `idle` is the calmest loop, not a frozen frame
- `working` should move more than `idle`
- `ready` should feel more energized than `working`
- `needsUserInput` should be the most attention-grabbing loop
