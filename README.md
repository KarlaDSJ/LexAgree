# LexAgree  
Agreement-based combination of multiple LLMs to improve legal argument annotation (premises and claims), outperforming single-model approaches.

## Overview  

This repository contains the code, data, and results associated with our approach for improving legal argument annotation through agreement across multiple large language models (LLMs).

## Repository structure  

- **`code/`**: Scripts for prompt execution, argument extraction, agreement computation (both intra- and inter-model), and evaluation, including similarity metrics and fine-grained analysis.  

- **`data/`**: Excel files where each sheet corresponds to a document from the corpus. These include:
  - Original (ground-truth) arguments  
  - Arguments extracted after prompting  
  - Arguments obtained after agreement (within the same LLM and across LLM pairs)  

- **`results/`**: Summary Excel file containing the evaluation results for all model configurations and agreement combinations.  

## Citation  

If you use this work, please cite:

```bibtex
% To be added