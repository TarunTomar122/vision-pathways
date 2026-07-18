# Fix Method Markdown Math Rendering

## Intended Commit Subject

`Fix method Markdown math rendering`

## Problem Or Decision

The formal route-search method rendered raw LaTeX delimiters on GitHub because it used `\\[` and
`\\]` for display math. The main README already uses GitHub's supported `$$` display-math syntax.
The decision is to normalize the method document to that same syntax without changing any equation
or claim.

## Files And Behavior Changed

- `paper/method.md` replaces all 18 `\\[` and `\\]` delimiter pairs with balanced standalone `$$`
  delimiters. Its 18 equations, notation, and prose are otherwise unchanged.

## Alternatives Considered

- Keeping the raw delimiters was rejected because GitHub displays them as literal text.
- Converting equations to images was rejected because images are less searchable, copyable, and
  accessible than MathJax-rendered text.
- Changing formulas or moving them into code blocks was rejected because this is a rendering repair,
  not a method revision.

## Verification Evidence

- Confirmed 36 standalone `$$` lines in `paper/method.md`, exactly two per display equation.
- Confirmed no remaining raw `\\[` or `\\]` delimiters in user-facing Markdown outside historical
  decision-log text and managed agent instructions.
- Ran `git diff --check`.

## Known Limitations And Unsupported Claims

- This verifies Markdown syntax statically. GitHub's live renderer remains the final display
  environment.
- The change does not revalidate the formulas, experimental results, or paper claims.

## Next Action Enabled

GitHub readers can now read the formal method with the same equation rendering used in the main
README.
