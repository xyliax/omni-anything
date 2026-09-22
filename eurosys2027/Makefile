LATEXMK ?= latexmk
MAIN := main.tex
SUPPLEMENT := supplement.tex
BUILD_DIR := build

# build/ holds latexmk's intermediate files only; the readable PDFs are copied
# to this directory as paper.pdf and supplement.pdf after every successful run.
LATEXMK_FLAGS := -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=$(BUILD_DIR)

.PHONY: all paper supplement check clean

all: paper

paper:
	$(LATEXMK) $(LATEXMK_FLAGS) $(MAIN)
	@cp $(BUILD_DIR)/main.pdf paper.pdf

supplement:
	$(LATEXMK) $(LATEXMK_FLAGS) $(SUPPLEMENT)
	@cp $(BUILD_DIR)/supplement.pdf supplement.pdf

check: paper
	bash scripts/check-submission.sh $(BUILD_DIR)/main.pdf

clean:
	$(LATEXMK) -C -outdir=$(BUILD_DIR) $(MAIN) $(SUPPLEMENT)
	rm -f paper.pdf supplement.pdf
