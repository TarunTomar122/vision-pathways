.PHONY: paper-assets verify-paper submission paper-pdf overleaf-package arxiv-package arxiv-preflight clean-paper-assets clean-paper-latex

PYTHON ?= python3

paper-assets:
	$(PYTHON) scripts/generate_paper_assets.py

verify-paper:
	$(PYTHON) scripts/verify_submission.py

submission: paper-assets verify-paper

paper-pdf: paper-assets
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

overleaf-package: paper-pdf
	cd paper && zip -FS -q overleaf-package.zip main.tex references.bib figures/*.pdf tables/generated-main-results.tex

arxiv-package: paper-pdf
	cd paper && zip -FS -q arxiv-source.zip main.tex references.bib figures/*.pdf tables/generated-main-results.tex

arxiv-preflight: arxiv-package
	$(PYTHON) scripts/arxiv_preflight.py

clean-paper-assets:
	rm -f paper/data/paper-data.json paper/tables/generated-* paper/figures/generated-*

clean-paper-latex:
	cd paper && latexmk -C main.tex
