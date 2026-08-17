from embeddings import *
import re
from functools import lru_cache
from typing import List
import numpy as np
from scipy.signal import find_peaks
from embeddings import _cosine

#all the section in ECHR documents
SECTION_HEADERS = [
    "PROCEDURE",
    "THE FACTS",
    "AS TO THE FACTS",
    "COMPLAINTS",
    "PROCEEDINGS BEFORE THE COMMISSION",
    "THE LAW",
    "AS TO THE LAW",
]

#sections to keep
KEEP_SECTIONS = {"COMPLAINTS", "THE LAW", "AS TO THE LAW"}

DISSENTING_OPINION_RE = re.compile(
    r"^DISSENTING OPINION OF (?:JUDGE|JUDGES)\s+[A-ZÀ-Ü.\s]+$", re.MULTILINE
)

def extract_relevant_sections(text: str) -> List[dict]:
    """Return [{"name", "start", "end", "text"}] only for the relevant sections"""

    #To find each section 
    header_alternatives = "|".join(re.escape(h) for h in SECTION_HEADERS)
    header_re = re.compile(
        rf"^[ \t]*[IVXLC0-9.]*[ \t]*({header_alternatives})[ \t]*$",
        re.MULTILINE,
    )

    #We identify the begining and the end of each title 
    matches = list(header_re.finditer(text))
    dissenting_matches = list(DISSENTING_OPINION_RE.finditer(text))
    all_headers = matches + dissenting_matches

    sections = []
    for i, sec in enumerate(all_headers):
        #start after the name of the section
        content_start, name = sec.end(), sec.group(1).strip()
        if name in KEEP_SECTIONS or name.startswith("DISSENTING OPINION"):
            #finish when star the next one
            content_end = all_headers[i + 1].start() if i + 1 < len(all_headers) else len(text)
            sections.append({
                "name": name,
                "start": content_start,
                "end": content_end,
                "text": text[content_start:content_end],
            })

    if not sections:
        # If we dont find relevant section we return all the document
        print("WARNING: No known section headers were detected. The entire document will be used.")
        sections = [{"name": "FULL_DOCUMENT", "start": 0, "end": len(text), "text": text}]

    return sections

@lru_cache(maxsize=1)
def _get_sat_model(model_name: str = "sat-3l-sm"):
    """Loads the model once per process"""
    from wtpsplit import SaT
    return SaT(model_name)


def sentence_segments_for_section(section: str, sat_model=None) -> List[str]:
    """identify the segments in a section
    section (str): the text of the section
    return (list) with the segments"""
    sat_model = sat_model or _get_sat_model()
    sentences = sat_model.split(section)
    return sentences

def merge_until_max(segments: List[str], max_size: int) -> List[str]:
    final = []
    aux = ""

    for segment in segments:
        if len(aux) + len(segment) > max_size:
            if aux:
                final.append(aux)
            aux = segment
        else:
            aux += segment
    if aux:
        final.append(aux)

    return final

def merge_adjacent_by_similarity(sentences: List[str], max_size: int = 5000) -> List[dict]:
    """
    1. Embed all sentences. 
    2. Calculate the cosine similarity between each sentence and the next one. 
    3. Detect topic shifts using `find_peaks()` on the dissimilarity
    (1 - similarity), a  peak there indicates a major topic shift. 
    4. Merge ADJACENT segments belonging 
    """
    if not sentences or len(sentences) == 1:
        return sentences

    #embeddings = embed_texts(sentences)
    #n = len(sentences)
 
    #adjacent_sims = np.array([_cosine(embeddings[i], embeddings[i + 1]) for i in range(n - 1)])
 
    #peak_idx, _ = find_peaks(1 - adjacent_sims)
    #cut_points = sorted(set(int(p) for p in peak_idx)) 
    #bounds = [0] + [c + 1 for c in cut_points] + [n] #add the start and the end with the cut points
    #natural_ranges = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]

    #segments = []
    #for start, end in natural_ranges:
    #    segments.append("\n".join(sentences[start:end]))

    return merge_until_max(sentences, max_size)

def make_segmentation(text: str, max_size: int = 5000) -> List[dict]:
    """Given a document, identifies sections that might contain arguments and segments them"""
    sections = extract_relevant_sections(text)

    sat_model = _get_sat_model()
    segments = []
    for section in sections:
        text = re.sub(r"\s+", " ", section["text"]).strip() #clean the spaces in text
        if len(text.split()) > max_size: 
          all_sentences = sentence_segments_for_section(text, sat_model)
          segments.extend(merge_adjacent_by_similarity(all_sentences, max_size))
        else:#if the section fit in the LLM we keep it
          segments.append(text)

    return segments