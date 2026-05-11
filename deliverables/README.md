# CourseWorks Deliverables

This directory holds the final files intended for the COMS E6998 CourseWorks submission.

> **Status note 2026-05-10 23:54 EDT:** the presentation PPTX and
> PDF listed below are the final CourseWorks presentation artifacts. The IEEE
> final report PDF listed below is also current.

## Contents

- `SmartGridBench-Final-Presentation.pptx` — final presentation deck source.
- `SmartGridBench-Final-Presentation.pdf` — final presentation PDF export.
- `SmartGridBench_Final_Paper.pdf` — IEEE-format final report.
- `archive/` — superseded Team13-named exports from the earlier PR #202 package,
  retained for traceability only.

## Provenance and regeneration

Each artifact is a one-shot export from a separately versioned source. Re-export after content changes; CourseWorks reviewers should treat the PDFs as exports of the listed sources at the export time below, not as independently authored documents.

### `SmartGridBench-Final-Presentation.pptx`

Final editable presentation source for the CourseWorks submission. Edited in PowerPoint / Keynote / LibreOffice Impress, then committed into the team repo for grader access.

### `SmartGridBench-Final-Presentation.pdf`

Final one-shot export from the PPTX above. To regenerate after a PPTX content change:

1. Open `SmartGridBench-Final-Presentation.pptx` in PowerPoint (or Keynote, or LibreOffice Impress).
2. File -> Export -> PDF -> 16:9 widescreen, embed fonts, "best for printing" quality.
3. Save over `SmartGridBench-Final-Presentation.pdf` in this directory.
4. Verify with `pdftotext deliverables/SmartGridBench-Final-Presentation.pdf - | grep -E "scenario|36 |61 "` that any scenario-count claims match `README.md` and `docs/final_presentation_deck.md`.

A scriptable PPTX → PDF conversion via LibreOffice headless mode is available on systems with `soffice` installed:

```bash
soffice --headless --convert-to pdf --outdir deliverables/ deliverables/SmartGridBench-Final-Presentation.pptx
```

The output may differ slightly from PowerPoint's native exporter (font fallback, slide-master rendering); for the submitted artifact prefer the PowerPoint export path above.

### `SmartGridBench_Final_Paper.pdf`

Built from an IEEE LaTeX source maintained outside this repo by the release owner. To regenerate, the release owner re-runs `pdflatex` (twice, for refs) on the source and copies the resulting `main.pdf` over `deliverables/SmartGridBench_Final_Paper.pdf` in this directory.

Verify the resulting PDF (run from the repo root):

```bash
pdfinfo deliverables/SmartGridBench_Final_Paper.pdf | grep -E "Pages|Producer"
pdftotext deliverables/SmartGridBench_Final_Paper.pdf - | grep -iE "claude|codex|chatgpt"
```

The AI-disclosure block must list Claude and Codex only (no ChatGPT). Page count should be within the IEEE class submission limit; verify with `pdfinfo` after each recompile (the literal page count rotates per .tex revision).

## Submission checklist

Before each export, confirm scenario-count claims are consistent across `README.md`, `docs/final_presentation_deck.md`, the report PDF, and the presentation PDF:

- Report/paper-grade evaluation: 36 validated scenarios (31 hand-authored + 5 promoted generated) + 5 negative fixtures. This is the evaluated corpus frozen at NeurIPS submission (2026-05-07).
- Final deck/public repo corpus: 61 current canonical scenario files in `data/scenarios/` + 5 negative fixtures, with the 31-scenario judged floor labeled separately in the deck.

Final presentation PDF SHA-256: `b941e411b4d550398705a8d1c90e11da08a59d303f4787e2a7c5ee7c38e0a742`.
Final presentation PPTX SHA-256: `9e291046dda7c16f5204a448ea2f18c116381d9eb4c69a6efe944024ef6658db`.
Final report PDF SHA-256: `6d75c0b500b0bc5fba15155c796215e7d1e88d309442821848a45a3af0f7f527`.

Last regenerated: see `git log -1 --format=%ci -- deliverables/SmartGridBench-Final-Presentation.pdf` and equivalent for the report PDF.
