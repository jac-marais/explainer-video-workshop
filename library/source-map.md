# Source map

The [manifest](manifest.json) maps stable IDs to canonical URLs. It contains primary documents, secondary/indexed observations, and failed discovery attempts. Counts are not independent-source counts, prevalence estimates, or quality scores.

## Retrieve by question

| Question | Source IDs | Readable evidence |
|---|---|---|
| Which examples disclose methods? | S-EX-001–025 | [Example atlas](notes/example-atlas.md) |
| Is the UMAP eight-hour run verified? | S-RUN-001–011 | Not verified. Original attribution and status remain unresolved; see the [example atlas](notes/example-atlas.md). |
| Which prompts and skills can I inspect? | S-TC-001–009, S-HF-003/009–011, S-PX-003 | [Skill map](notes/prompt-and-skill-map.md) with pinned original URLs |
| What does HyperFrames actually support? | S-HF-001–011 | [Production paths](notes/production-paths.md); original URLs in the manifest |
| What is public versus hosted in Pexo? | S-PX-001–007 | [Production paths](notes/production-paths.md); original URLs in the manifest |
| How do alternative renderers handle narration/timing/review? | S-TC-001–008 | [Production paths](notes/production-paths.md), [skill map](notes/prompt-and-skill-map.md) |
| What does the model/time-budget evidence prove? | S-FA-001–004/009 | Vendor-stated interfaces and limits only; original URLs in the manifest |
| What makes an explainer useful for learning? | S-FA-006–008 | Brame review, Guo metadata, and Niekrenz/Spreckelsen review; original URLs in the manifest. Engagement is not a transfer/retention measure. |
| Which voice options are local? | S-VO-001/002, S-TC-003 | [Production paths](notes/production-paths.md); original URLs in the manifest |

## Authority and retention

Official model documentation establishes vendor-stated interfaces and limits. Framework repositories establish published implementation contracts at a revision. Neither establishes an independently reproduced production result. Creator posts establish attributed reports only when the original is inspected; when originals are inaccessible, the receipt identifies the intermediary instead. The social atlas here is predominantly index-derived.

In the source-linked index, sampled frames were inspected by its author. This workshop did not inspect those videos' motion or audio. The index explicitly says it is selective and not a benchmark. Failure and access records remain in the manifest so later work can avoid dead ends; they are not positive support.

Short excerpts, paraphrases, exact locators, versions, and original synthesis are retained. Full videos, copyrighted source collections, raw private transcript text, and downloaded third-party projects are not vendored. See [source use](source-use-policy.md).
