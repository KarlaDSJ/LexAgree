# LexAgree

Agreement-based combination of multiple LLMs to improve legal argument
annotation (premises and claims), outperforming single-model approaches.

## Overview

This repository contains the code, data, and results associated with our
approach for improving legal argument annotation through agreement across
multiple large language models (LLMs), along with an interactive web
interface for running the pipeline on new documents.

## Repository structure

- **`code/`**: Scripts for prompt execution, argument extraction, agreement
  computation (both intra- and inter-model), and evaluation, including
  similarity metrics and fine-grained analysis.

- **`data/`**: Excel files where each sheet corresponds to a document from
  the corpus. These include:
  - Original (ground-truth) arguments
  - Arguments extracted after prompting
  - Arguments obtained after agreement (within the same LLM and across LLM
    pairs)

- **`results/`**: Summary Excel file containing the evaluation results for
  all model configurations and agreement combinations.

- **`backend/`**: FastAPI service that runs the pipeline (segmentation →
  multi-LLM extraction → alignment → agreement) on user documents. 

- **`frontend/`**: React web interface to upload a document, pick which
  models to consult, and browse the resulting arguments highlighted in the
  original text. 


### Quick start

```bash
# Terminal 1 — API
cd argument-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn main:app --reload --port 8000


# Terminal 2 — web interface
cd argument-ui
npm install
npm run dev
```

Then open `http://localhost:5173` for the web interface.

## Citation

If you use this work, please cite:

```bibtex
% To be added
```
