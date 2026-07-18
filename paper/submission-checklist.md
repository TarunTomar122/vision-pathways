# Submission Checklist

## Scientific Audit

- [ ] Every task-versus-generic comparison uses the same K.
- [ ] Processed-v2 is called method-selection evidence, not sealed external evidence.
- [ ] SmolVLM appears only at K4 in completed-result plots.
- [ ] The IIIT5K negative transfer result is in the abstract or main text.
- [ ] Confidence intervals that cross/touch zero are not described as confirmed wins.
- [ ] Parameter, latency, and checkpoint-size claims are distinguished.
- [ ] Qwen final-route latency is described as missing rather than inferred.
- [ ] One independent ML researcher has checked aggregation, splits, claims, and novelty.

## Manuscript Package

- [ ] Author names, affiliations, email, ORCID, acknowledgements, and funding are supplied.
- [ ] Title and abstract match the final PDF and arXiv metadata.
- [ ] All figure text is readable at one-column or two-column width.
- [ ] Tables use `booktabs`; captions state examples, split, metric, and uncertainty.
- [ ] Appendix includes routes, seeds, hashes, and search configuration.
- [ ] Repository URL and commit/tag are included in the manuscript.
- [ ] A release tag is created after the manuscript assets are frozen.
- [ ] A software license and data-license notes are selected by the author.

## Human And AI Review

- [ ] The human author has read every sentence and can explain every equation, design choice, result,
  limitation, and conclusion without relying on an AI transcript.
- [ ] Every cited paper has been opened at its primary source, and its title, authors, venue, year,
  identifier, and claimed relevance have been checked manually.
- [ ] Every number in the abstract, figures, tables, and conclusion has been traced to committed
  evidence or a named analysis artifact.
- [ ] The target conference or journal's current generative-AI policy has been checked separately;
  arXiv is a repository, not a substitute for the venue's authorship and disclosure rules.
- [ ] No AI system is listed as an author. The human author accepts responsibility for the submitted
  text, code, experiments, citations, and claims.
- [ ] Substantive AI assistance is disclosed wherever the target venue requires it. If no venue form
  exists, consider a concise acknowledgements statement such as:

> AI-assisted tools were used for code assistance, experiment orchestration, figure generation,
> manuscript organization, and language editing. The author reviewed the resulting code, evidence,
> citations, analysis, and text and takes responsibility for the final work.

- [ ] The disclosure above is included only after its final sentence is true. Human review cannot be
  replaced by adding a disclosure.
- [ ] No confidential credentials, restricted images, private review material, or personal data were
  included in prompts or submission files.

## arXiv

- [ ] Sign in to a registered arXiv author account. Start a draft submission early to discover whether
  first-time or `cs.CV` endorsement is required.
- [ ] If endorsement is required, use the code from arXiv to contact one appropriate researcher who
  knows the author or the work. Do not mass-email endorsers.
- [ ] Freeze author names, affiliations, email, ORCID, title, abstract, comments, and categories.
- [ ] Use `cs.CV` as the intended primary category. Add `cs.LG` or `cs.CL` only when the paper's
  content genuinely supports the cross-list.
- [ ] Choose the distribution license deliberately. The choice is irrevocable; check future venue and
  funder rules before selecting CC BY or another option.
- [ ] Prepare a source ZIP containing `main.tex`, `references.bib` or matching `main.bbl`, all eight
  PDF figures, and `tables/generated-main-results.tex` with their relative directories intact.
- [ ] Run `make arxiv-package` if the repository version is final, or use Overleaf's arXiv source
  export if Overleaf contains newer edits. Do not upload an archive without knowing which version won.
- [ ] Remove compiled PDFs, auxiliary files, caches, model weights, raw restricted images,
  credentials, and unrelated repository files from the upload ZIP.
- [ ] On arXiv, choose **Start New Submission**, upload the ZIP, click **Check Files**, select
  **pdfLaTeX** if it is not detected, and confirm `main.tex` as the top-level file.
- [ ] Review arXiv's suggested file deletions before accepting them. Do not let it remove a referenced
  figure, table, bibliography, or required source file.
- [ ] Open the arXiv-generated PDF and inspect every page, figure, table, reference, hyperlink,
  author field, and page count. A local or Overleaf compile is not sufficient.
- [ ] Enter metadata manually and confirm that the title and abstract exactly match the PDF. Complete
  the license and submission agreement screens, then submit.
- [ ] If an error is found before announcement, use **Unsubmit**, correct the existing submission, and
  resubmit. Do not create a second paper entry.
- [ ] After announcement, add the arXiv URL and identifier to the website, README, `CITATION.cff`, and
  paper references; create a release tag for the submitted commit.

Official references:

- Submission process: https://info.arxiv.org/help/submit/index.html
- TeX and bibliography requirements: https://info.arxiv.org/help/submit_tex.html
- Endorsement: https://info.arxiv.org/help/endorsement.html
- Irrevocable license choice: https://info.arxiv.org/help/license/index.html

As checked on 2026-07-18, the official arXiv author guide does not state a separate generative-AI
disclosure field. That does not remove the human author's responsibility or any stricter policy from a
conference, journal, employer, or funder.

## Website/Wix

- [ ] Run `make submission` and inspect `docs/index.html` locally.
- [ ] Replace the paper placeholder with the final arXiv URL.
- [ ] Add author/affiliation information after approval.
- [ ] Publish `docs/` with GitHub Pages, or recreate its sections in Wix using the supplied copy.
- [ ] Verify mobile layout, figure alt text, repository link, and caveat text.
