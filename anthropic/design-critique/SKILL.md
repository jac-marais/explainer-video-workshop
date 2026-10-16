---
name: design-critique
description: Get structured design feedback on an explainer storyboard's usability, hierarchy, and consistency. Trigger with "review this storyboard", "critique this storyboard", or when a run's storyboard.html is ready for feedback at any stage from exploration to final polish.
argument-hint: "<path to storyboard.html>"
---

# /design-critique

Get structured design feedback across multiple dimensions.

## Usage

```
/design-critique $ARGUMENTS
```

Review the design: @$1

Read the storyboard, the run's brief, and the brand file that `local/brand.md` names. If no storyboard is given, ask for its path.

## What I Need From You

- **The design**: the run's `storyboard.html`
- **Context**: the run's brief, which says who the film is for, what they should understand, and the pacing
- **Focus** (optional): "Focus on scene 3" or "Focus on the captions"

## Critique Framework

### 1. First Impression (2 seconds)
- What draws the eye first? Is that correct?
- What's the emotional reaction?
- Is the purpose immediately clear?

### 2. Usability
- Can the viewer follow the explanation?
- Does each frame show what its narration says, at the words that cue it?
- Is each movement a planned beat, under the beat rule in step 4 of `methods/prepare-explainer-video.md`?
- Are there unnecessary steps?

### 3. Visual Hierarchy
- Is there a clear reading order?
- Are the right elements emphasized?
- Is whitespace used effectively?
- Is typography creating the right hierarchy?

### 4. Consistency
- Does it follow the brand file? The `brand-explainer-video` skill owns the full audit.
- Are spacing, colors, and typography consistent?
- Do similar elements behave similarly?
- Does it break any principle in `anthropic/frontend-design/SKILL.md`, or fall into one of the generic defaults that skill lists?

### 5. Accessibility
- Color contrast ratios
- Smallest text and line sizes, read on a phone screen
- Text readability, and time on screen to read it
- Narration that says what the viewer must see, for a viewer who cannot see the picture
- Color never the only cue
- Nothing flashing more than three times a second
- Captions that match the narration, with nothing drawn in their band

## How to Give Feedback

- **Be specific**: "The headline competes with the diagram" not "the layout is confusing"
- **Explain why**: Connect feedback to design principles or viewer needs
- **Suggest alternatives**: Don't just identify problems, propose solutions
- **Acknowledge what works**: Good feedback includes positive observations
- **Match the stage**: Early exploration gets different feedback than final polish

## Output

```markdown
## Design Critique: [Design Name]

### Overall Impression
[1-2 sentence first reaction — what works, what's the biggest opportunity]

### Usability
| Finding | Severity | Recommendation |
|---------|----------|----------------|
| [Issue] | 🔴 Critical / 🟡 Moderate / 🟢 Minor | [Fix] |

### Visual Hierarchy
- **What draws the eye first**: [Element] — [Is this correct?]
- **Reading flow**: [How does the eye move through the layout?]
- **Emphasis**: [Are the right things emphasized?]

### Consistency
| Element | Issue | Recommendation |
|---------|-------|----------------|
| [Typography/spacing/color] | [Inconsistency] | [Fix] |

### Accessibility
- **Color contrast**: [Pass/fail for key text]
- **Smallest text**: [Readable on a phone?]
- **Text readability**: [Font size, line height, time on screen]
- **Picture in the narration**: [Can a viewer follow without seeing it?]
- **Captions**: [Match the narration, band clear?]

### What Works Well
- [Positive observation 1]
- [Positive observation 2]

### Priority Recommendations
1. **[Most impactful change]** — [Why and how]
2. **[Second priority]** — [Why and how]
3. **[Third priority]** — [Why and how]
```

## Tips

1. **Share the context** — "This is a two-minute explainer for new engineers" helps me give relevant feedback.
2. **Specify your stage** — Early exploration gets different feedback than final polish.
3. **Ask me to focus** — "Just look at scene 3" gives you more depth on one area.

---

Adapted from `design/skills/design-critique/SKILL.md` in [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) at commit `33eeda1`, under the Apache License 2.0 in `LICENSE` beside this file. Changed for video storyboards: the input is `storyboard.html`, the connector and Figma parts are removed, and the usability and consistency checks are about narration, beats and the brand file instead of screens, consistency also checks the principles in `anthropic/frontend-design/SKILL.md`, and the accessibility checks are their film counterparts, such as phone-size text for touch targets and narration that carries the picture for alternative text.
