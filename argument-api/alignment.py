import difflib
from typing import Optional
import re
from typing import List
from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer


_SENTENCE_SPLIT_RE = re.compile(r'(?:(?<=[.!?])\s+)|(?:\n\s*\n\s*)')

def semantic_best_span(original_text: str, snippet: str) -> Optional[dict]:
    """Encuentra la mejor oración del documento original más parecida
    semánticamente a `snippet` (que puede estar parafraseado por un LLM).
    """
    sentence_texts = _SENTENCE_SPLIT_RE.split(original_text)

    texts = sentence_texts + [snippet]
    embeddings = embed_texts(texts)
    snippet_emb = embeddings[-1]

    sims = [_cosine(embeddings[i], snippet_emb) for i in range(len(sentence_texts))]
    best_idx = int(np.argmax(sims))
    best = texts[best_idx]
    id = original_text.find(best)

    return {
        "start": id,
        "end": id + len(best),
        "match_ratio": round(float(sims[best_idx]), 3)
    }

def find_best_span(original_text: str, snippet: str, threshold) -> Optional[dict]:
    """Returns {"start", "end", "match_ratio"} for the best match of `snippet`
    within `original_text` using exact matching, or None if the snippet is empty."""
    snippet = snippet.strip()
    idx = original_text.find(snippet)
    if idx != -1:
        return {"start": idx, "end": idx + len(snippet), "match_ratio": 1.0}

    split_text = _SENTENCE_SPLIT_RE.split(original_text)
    matches = difflib.get_close_matches(
        snippet, 
        split_text, 
        n=1,         # Max results
        cutoff=threshold
    )
    if matches:
        id = original_text.find(matches[0])
        return {"start": id, "end": id + len(matches[0]), "match_ratio": threshold}
    
    return None

def align_snippet(original_text: str, snippet: str,threshold: float = 0.80) -> Optional[dict]:
    """Search for exact or very similar matches without using embeddings"""
    literal = find_best_span(original_text, snippet, threshold)
    if not literal:
        literal = semantic_best_span(original_text, snippet)

    return literal


def do_alignment(original_text: str, llm_args: dict) -> List[dict]:
    """
    llm_args: { "name_llm": ["arg_1", "argu_2", ...], ... }
    Return: { "name_llm": [ {"text", "start", "end", "match_ratio"}, ... ] }
    """
    aligned = {}
    for llm_name, arg_texts in llm_args.items():
        spans = []
        for arg_text in arg_texts:
            per_sentence = arg_text.split() #We break down the argument by component
            for sentence in per_sentence:
              span = align_snippet(original_text, sentence)
              if span is not None:
                  spans.append({"text": sentence, **span})
        aligned[llm_name] = spans
    return aligned