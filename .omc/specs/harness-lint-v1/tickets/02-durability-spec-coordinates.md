# T2 — durability/spec-coordinates + standard correction

- **id:** T2
- **blockedBy:** [T1]

## Output
Rule 2 wired through the same pipeline as T1, catching path coordinates in markdown under the specs directory, with the C2 #1 refinement and the associated standard-document correction (the data standard's predicate wording was itself wrong; correcting it is in this run's scope).

## Crosses every layer
- **Rules** — rule 2 pure function: markdown -> violations, one per path-coordinate token. Coordinate predicate (refined, C2 #1): a token whose **final `/`-segment contains a dot, or that ends with `/`**. So `src/store.js` and `path/to/` are coordinates; `context-md/entry-format` (final segment has no dot) is not. Tokenization splits on whitespace and strips trailing/leading punctuation (`)`, `]`, `}`, `)`, `,`, `.` and `(`/`[`).
- **Exemptions**
  - Line carrying the inline marker `<!-- origin-fragment -->` is exempt whole-line.
  - CJK exemption (the F-0008 lesson): a token bordering a CJK character on either side, or containing a CJK character, is exempt.
- **Engine/registry** — rule registered with severity high; reuse T1's runner unchanged (this slice adds zero engine changes — separation of concerns dogfood).
- **Dispatcher (router)** — any markdown under a directory segment named `specs` -> rule 2.
- **CLI** — mounts automatically via registry; no CLI change.
- **Docs (in-scope correction)** — the data standard's rule-2 predicate wording updated to the refined predicate, with an errata note recording the C2 #1 origin; kept consistent with this spec's Implementation Decisions entry.

## Demonstrable smoke
- A spec doc containing `src/store.js` -> one high violation; a line with `<!-- origin-fragment -->` plus a `src/store.js` -> exempt; a CJK-adjacent pass, e.g. `关于/src/store.js` bordered by CJK -> exempt; a rule-identifier token like `context-md/entry-format` -> NOT flagged (the regression the refinement fixes).

## Accepts
- T2 is complete when the refined predicate, both exemptions, and the rule-identifier non-match are asserted via seam S2, the router case via S4, and at least one end-to-end JSON/human smoke via S5/S6; and the standard-document correction + spec note are on disk.

## Note
- Directory-address `src/store` (no ext, no trailing slash) is intentionally not flagged — accepted v1 gap (C2 #1).