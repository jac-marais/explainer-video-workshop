# Comic craft for narrated explainers and vertical Shorts

These are craft techniques from comics. No learning study backs these adaptations yet. The rules in the [preparation method](prepare-explainer-video.md) win if they conflict.

## Solve it in the writing first

If a scene's meaning or feeling is unclear, repair the script before adding lettering, motion or color.

The preparation method's [cast rules](prepare-explainer-video.md#cast) apply to every technique here.

## Scripting and layout

### Text-first shots

Translate a panel into a shot, panel size into screen time and framing, and a gutter into a cut or transition. Before drawing, describe each shot's action in text. For an invented queue explainer, the sequence could be a wide view of items arriving, a close view of one item waiting, then a wider view as another worker starts taking items. Choose which moment deserves the closest framing and the most time before building the scene.

In a vertical Short, compose the action for the narrow frame from the start. A horizontal row of comic panels usually becomes a sequence of shots, rather than a shrunken page. Use the [scene-plan template](../templates/scene-plan.md) for the shot descriptions and timing budget.

The [starter composition](../templates/composition/README.md#caption-layout) uses 1920×1080 geometry; vertical delivery needs a layout adaptation and delivery-size checks before production can rely on it.

### Reading order

Translate balloon order into the order in which the viewer encounters actions and their labels. In an English-language diagram, an upper element followed by a lower one can guide the eye when a left-to-right arrangement would crowd the vertical frame. Follow the audience's reading direction, and rearrange the layout so that connectors never cross.

For example, reveal a filter above a storage tray, then move an item between them. If both must stay visible, make the active step clear through its action rather than making the viewer choose between simultaneous reveals.

### Inside and outside views

Use paired views when the lesson needs to compare an observable result with the hidden process that produces it. For example, show a progress indicator advancing, then cut inside the mechanism to show work waiting behind one slow operation. Keep a shared object or position across the cut so the viewer recognizes the same event. On a narrow screen, successive views can replace a cramped split screen.

Use the preparation method's [claim map](prepare-explainer-video.md#2-build-the-claim-map-before-prose) to ground the hidden view.

## Lettering and captions

For the video equivalent of a comic balloon, use the narration caption layer. Put any proposed extra text through the preparation method's [screen-text rule](prepare-explainer-video.md#4-convert-the-narrative-into-a-scene-and-shot-sequence). For caption fonts and geometry, use [caption layout](../templates/composition/README.md#caption-layout). Keep narration captions plain, steady in size and outside any effect; put each treatment below on the pictured object instead, because a styled caption costs readability without explaining anything.

### Hesitant narration

Use this when the narration voices a hesitation the lesson needs, such as a learner's first guess before the misconception beat breaks it. Keep a filler such as "um" when it carries that hesitation, and mark a deliberate pause before a sentence with `[pause]`. Pin each gesture or reaction to the quoted words after its pause. Spread those actions over shots so the picture carries the halting rhythm instead of squeezing it into one busy frame.

For example, the narrator says, "Um, the first route looks clear. [pause] The next item still cannot pass." A silent character tries the route, waits, then notices the obstruction.

The [caption builder](../scripts/audio/captions.py) breaks captions by line width and grammar, not by pause; separately timed caption phrases need a change to that script first.

### Quiet-to-urgent contrast

Use the small-to-large balloon idea when a quiet condition becomes an urgent consequence. Translate size into framing and action, such as moving from a distant gauge to a close view of a valve closing. The narration supplies the change in meaning.

### Sound and material cues

Use auditory or pictorial lettering ideas when the physical property is itself part of the lesson. A vibrating enclosure can show where a hum originates; a granular fill inside a container can distinguish a powder from a solid block. Keep the object's short name legible.

### Encoded notation

Use dots, dashes or another encoding only when the learner needs to read that notation. In an invented signaling lesson, show the Morse symbol for the letter N beside the label `N`, while the narration explains the dash followed by a dot. Reveal the sequence in order and leave time to compare the symbol with its decoded value. Decorative coded borders add another puzzle without teaching the encoding.

### Progressive corruption

Use staged corruption when degradation is the mechanism being taught. For an invented damaged-image example, keep a clean reference beside a version that loses a few blocks and then more blocks. Each stage needs a visible change in the represented data.

The [rendering routes](../library/renderers.md) provide no shared corruption effect; build and verify it in the chosen scene renderer before depending on it.

## Color

### Character rollout coloring

Use character rollout coloring when a character's world expands. Begin with a restricted palette that reflects the character or scene's inner state, then visibly widen it when a new person or idea enters. For example, a silent guide sees only a local path in muted violet; a view of the wider network introduces a pale gold accent as additional destinations become reachable. Let the shift carry the story beat before the narration explains it.

Record the before and after palettes and the triggering cue in the scene plan. Stay within the brand's color constraints, preserve established prop and data color meanings, and keep the action readable without color alone. The preparation method's [beat rule](prepare-explainer-video.md#4-convert-the-narrative-into-a-scene-and-shot-sequence) owns when this shift is permitted.

### Palette and mood

Try two palettes on the same key frame before choosing a scene's atmosphere. For example, compare a low-contrast slate background with a high-contrast plum background around the same neutral machine. Draw both drafts from the brand's palette roles. Judge the intended mood from the actual frame instead of assuming that a hue has one universal meaning.

This is a choice between drafts. Carry the selected palette through the scene; it is not an instruction to animate a palette swap during playback.

## Final watch-through

Watch the sequence in order at its intended delivery size, including the narrow frame for a vertical Short. Note any cut, label, caption treatment or palette choice that pulls attention away from the explanation. Check that the planned pauses, emphasis and changes of view land without stopping to reread. Fix each snag at the writing or scene stage that caused it. Use the preparation method's [production checks](prepare-explainer-video.md#8-run-machine-checks-and-bounded-checkpoints) for acceptance.
