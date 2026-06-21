# ShieldX Graduation Thesis

**Author**: Nguyen Quang Trung — trung.nq225557@sis.hust.edu.vn  
**Supervisor**: PhD. Nguyen Huu Duc  
**Program**: Cyber Security  
**School**: School of Information and Communications Technology, Hanoi University of Science and Technology  

## Project Title

**ShieldX: An Intelligent Endpoint Security Agent for Malware Detection over DNS-over-HTTPS using Machine Learning**

## Overview

This repository contains the LaTeX source code for the graduation thesis on ShieldX — an intelligent endpoint security agent that detects malware communication over DNS-over-HTTPS (DoH) using machine learning. The system comprises a Python-based endpoint agent for real-time packet capture and XGBoost classification, and a web dashboard (FastAPI + React) for centralized management.

## Repository Structure

```
reports/
├── main.tex              # Main LaTeX file — compile this to generate the PDF
├── main.pdf              # Compiled thesis (generated output)
├── reference.bib         # Bibliography references (BibTeX)
├── glossary.tex          # List of abbreviations (acronyms)
├── lstlisting.tex        # Code listing style configuration
├── Cover.tex             # Front cover page
├── Cover2.tex            # Inner cover page
├── Chapter/
│   ├── 0_2_acknowledgment.tex
│   ├── 0_3_abstract.tex
│   ├── 1_Introduction.tex
│   ├── 2_Survey.tex
│   ├── 3_Methodology.tex
│   ├── 4_Experiment_evaluation.tex
│   ├── 5_Solution_contribution.tex
│   ├── 6_Conclusion.tex
│   ├── 7_Reference.tex      # Reference format guidelines
│   ├── Appendix_A.tex        # Thesis writing guidelines
│   └── Appendix_B.tex        # Use case descriptions
├── Figure/
│   ├── Bia.PNG, GayBia.png, IoT.png, ...
│   ├── Chapter2/             # Use case diagrams
│   ├── Chapter3/             # Architecture & pipeline diagrams
│   ├── Chapter4/             # System design & UI screenshots
│   └── Chapter5/             # Communication flow diagrams
├── texmf/                    # LaTeX style files
└── README.md
```

## How to Compile

To generate the PDF from source, run the following commands **in the `reports/` directory**:

```bash
# Step 1: Compile LaTeX (first pass)
pdflatex -shell-escape main.tex

# Step 2: Generate bibliography
bibtex main

# Step 3: Generate glossary
makeglossaries main

# Step 4: Compile LaTeX (second pass to resolve references)
pdflatex -shell-escape main.tex

# Step 5: Compile LaTeX (third pass for all cross-references)
pdflatex -shell-escape main.tex
```

Or use a LaTeX IDE (e.g., TeXstudio, Overleaf) and compile with **pdflatex → bibtex → makeglossaries → pdflatex → pdflatex**.

## Figures

All figure files are in the `Figure/` directory. Placeholder images (gray boxes with descriptions) are provided where actual diagrams are needed. Replace them with your own diagrams before final submission.

## Notes

- The appendix section and "Short Notices on Reference" chapter are currently commented out in `main.tex`. Uncomment them if needed.
- The thesis uses IEEE citation style via BibTeX.
- Vietnamese language support is enabled via the `vietnam` package.
