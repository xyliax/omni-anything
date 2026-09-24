# ACM Template Provenance

Venue requirements rechecked against the official CFP on 2026-09-24; the pinned template files were not changed. The submission checklist is maintained in [`planning/submission-checklist.md`](../../planning/submission-checklist.md).

## Why This Template Was Selected

The official [EuroSys 2027 Call for Papers](https://2027.eurosys.org/cfp.html) explicitly encourages authors to use the ACM SIGPLAN LaTeX or MS Word templates. This workspace uses the SIGPLAN mode of ACM's `acmart` class.

## Pinned Release

- Upstream repository: `https://github.com/borisveytsman/acmart.git`
- Stable release tag cloned: `v2.20`
- Annotated tag object: `742841bea00b99d9f868ba7d7c3e03b4cb72b36e`
- Resolved commit: `10d6d082e522c4034022f38437019ba75589456b`
- Class declaration: `2026/08/16 v2.20 Typesetting articles for the Association for Computing Machinery`
- Retrieved and verified: 2026-08-25
- License: LPPL 1.3; see [`LICENSE`](LICENSE)

The rolling GitHub `primary` branch identifies itself as development/experimental. This workspace therefore does not follow `primary`; it pins the stable `v2.20` release.

## Production Cross-Check

The source files from the cloned `v2.20` tag were compared with the production archive served by CTAN:

`https://mirrors.ctan.org/macros/latex/contrib/acmart.zip`

The SHA-256 values for `acmart.dtx`, `acmart.ins`, and `ACM-Reference-Format.bst` matched byte-for-byte. The locally vendored `acmart.cls` and `samples/sigplan.tex` were generated from those pinned sources using their supplied `.ins` files.

Exact local file hashes are stored in [`SHA256SUMS`](SHA256SUMS).

## Local Review Configuration

`main.tex` uses:

```tex
\documentclass[sigplan,10pt,anonymous,review]{acmart}
\settopmatter{printfolios=true,printacmref=false}
```

This deliberately combines:

- `sigplan`: the venue-recommended two-column ACM family;
- `10pt`: EuroSys' minimum text-size requirement;
- `anonymous`: double-blind author suppression;
- `review`: reviewer-friendly line numbering;
- `printfolios=true`: mandatory page numbers.

EuroSys-specific instructions override the generic `acmart` sample comment that suggests a one-column manuscript mode for some ACM review workflows. EuroSys explicitly requires two columns and recommends SIGPLAN.

## Limits of the Trust Claim

This provenance supports confidence that the class is an authentic, pinned ACM production release and that the selected mode matches the EuroSys 2027 CFP. It does not guarantee that a paper is submission-compliant: authors can still exceed 12 technical pages, leak identity, use unreadable figures, alter geometry, or miss a later rule update. The official CFP and HotCRP instructions remain final authority and must be rechecked on submission day.
