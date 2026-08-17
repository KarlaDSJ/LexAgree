"""
Cleaning and parsing the raw responses from LLMs for
argument extraction. The format expected by the prompt is:

    1. Argument
    **Claim:** {claim}
    **Premises:**
    - {premise 1}
    - {premise 2}

but in practice, the models vary: no bold text, no numbering,
“Claim:” in lowercase, extra text before or after, placeholders such as
“None explicitly stated in the text.” instead of omitting the section, bullet points
using “-”, “*”, “•”, or numbered lists, isolated comments from the model mixed in with
the premises, etc.
"""

import re
from typing import Dict, List

_PLACEHOLDER_RE = re.compile(
    r'\bnone\s+explicitly\s+stated(?:\s+in\s+the\s+text)?\.?'
    r'|\bnone\s+mentioned(?:\s+in\s+the\s+text)?\.?'
    r'|\bnone\s+provided(?:\s+in\s+this\s+claim)?\.?'
    r'|\bnot\s+applicable\.?'
    r'|\bn/?a\b\.?'
    r'|\bnone\b\.?',
    re.IGNORECASE,
)

_ARGUMENT_SPLIT_RE = re.compile(
    r'(?:^|\n)\s*(?:\*\*)?\s*\d*\.?\s*Argument\s*\d*\s*:?\s*(?:\*\*)?\s*(?=\n|$)',
    re.IGNORECASE,
)

_CLAIM_RE = re.compile(r'\*{0,2}\s*Claim\s*[:*\s]*', re.IGNORECASE)

_PREMISES_RE = re.compile(r'\*{0,2}\s*Premises?\s*[:*\s]*', re.IGNORECASE)

_BULLET_RE = re.compile(r'^\s*(?:[-*•]|\d+[.)])\s*(.+)$')

MIN_PREMISE_LENGTH = 8  # discards fragments that are too short to be a real premise


def _strip_placeholders(text: str) -> str:
    return _PLACEHOLDER_RE.sub('', text).strip(' .\n')


def _extract_premises(block: str) -> List[str]:
    """Of everything that follows **Premises:**, it keeps only lines that
    take the form of actual vignettes. """
    premises = set()
    for line in block.split('\n'):
        line = line.strip()
        m = _BULLET_RE.match(line) #vignettes?
        if m:
            candidate = _strip_placeholders(m.group(1).strip())
            if not candidate or len(candidate) < MIN_PREMISE_LENGTH:
                continue
            premises.add(candidate)
    return list(premises)


def parse_llm_response(raw_text: str) -> List[Dict[str, object]]:
    """
    Parses the raw response from an LLM (for a segment) into a list of
    structured arguments.

    Returns: [{“claim”: str, “premises”: [str, ...]}, ...]

    A block without an identifiable **Claim:** is discarded
    """
    if not raw_text or not isinstance(raw_text, str):
        return []

    blocks = _ARGUMENT_SPLIT_RE.split(raw_text)
    if len(blocks) == 1:
        blocks = [raw_text]

    results = []
    for block in blocks:
        if not block.strip():
            continue

        claim_match = _CLAIM_RE.search(block)
        if not claim_match:
            continue  # no claim, no argument

        after_claim = block[claim_match.end():]
        premises_match = _PREMISES_RE.search(after_claim)

        if premises_match:
            claim_text = after_claim[:premises_match.start()]
            premises_text = after_claim[premises_match.end():]
        else:
            claim_text = after_claim
            premises_text = ''

        claim = ' '.join(claim_text.split())  
        claim = _strip_placeholders(claim)
        if not claim:
            continue

        premises = _extract_premises(premises_text)
        results.append({"claim": claim, "premises": premises})

    return results


def clean_llm_response(raw_text: str) -> List[str]:
    """
    Same as `parse_llm_response`, but serializes each argument as a single
    string: “premise1\\npremise2\\n...\\nclaim”
    """
    parsed = parse_llm_response(raw_text)
    out = set()
    for arg in parsed:
        text = '\n'.join([*arg["premises"], arg["claim"]])
        out.add(text)
    return list(out)