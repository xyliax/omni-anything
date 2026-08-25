LATEXMK ?= latexmk
MAIN := main.tex
SUPPLEMENT := supplement.tex
BUILD_DIR := build

.PHONY: all paper supplement check clean

all: paper

paper:
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD_DIR) $(MAIN)

supplement:
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD_DIR) $(SUPPLEMENT)

check: paper
	bash scripts/check-submission.sh $(BUILD_DIR)/main.pdf

clean:
	$(LATEXMK) -C -outdir=$(BUILD_DIR) $(MAIN) $(SUPPLEMENT)
