"""
Extracts symbolic claims from a natural language or structured premise.
Returns a normalized dict of claim type, direction, magnitude, and units.
"""

import re

ENERGY_KEYWORDS  = ["energy","heat","power","work","entropy","temperature","joule","watt","kelvin"]
MASS_KEYWORDS    = ["mass","matter","resource","material","weight","kilogram","ton","supply"]
FLOW_KEYWORDS    = ["transfer","move","extract","produce","consume","generate","destroy","create"]

def parse_premise(premise: str) -> dict:
    p = premise.lower()
    keywords = _extract_keywords(p)
    claim = {
        "raw"        : premise,
        "type"       : _detect_type(p),
        "direction"  : _detect_direction(p),
        "magnitude"  : _extract_magnitude(p),
        "negations"  : _count_negations(p),
        "keywords"   : keywords,
        "negated_kw" : _find_negated_keywords(p, keywords),
    }
    return claim

def _detect_type(p):
    if any(k in p for k in ENERGY_KEYWORDS):  return "thermodynamic"
    if any(k in p for k in MASS_KEYWORDS):    return "mass_balance"
    return "unknown"

def _detect_direction(p):
    if any(k in p for k in ["increase","more","gain","grow","add"]): return "positive"
    if any(k in p for k in ["decrease","less","lose","shrink","remove"]): return "negative"
    return "neutral"

def _extract_magnitude(p):
    nums = re.findall(r'\d+\.?\d*', p)
    return [float(n) for n in nums] if nums else [1.0]

def _count_negations(p):
    words = re.findall(r"[a-z']+", p)
    negation_words = {"not", "no", "never", "without", "cannot", "can't"}
    return sum(1 for w in words if w in negation_words)

def _find_negated_keywords(p, keywords):
    """Find keywords that are preceded by a negation word (within 3 words)."""
    words = re.findall(r"[a-z']+", p)
    neg_words = {"not", "no", "never", "without", "cannot", "can't"}
    negated = []
    for i, w in enumerate(words):
        if w in neg_words:
            # check next 3 words for keyword stem matches
            for j in range(i + 1, min(i + 4, len(words))):
                for kw in keywords:
                    if words[j].startswith(kw) or kw.startswith(words[j]):
                        if kw not in negated:
                            negated.append(kw)
    return negated

def _extract_keywords(p):
    words = re.findall(r"[a-z]+", p)
    all_kw = ENERGY_KEYWORDS + MASS_KEYWORDS + FLOW_KEYWORDS
    return [k for k in all_kw if any(w.startswith(k) or k.startswith(w) for w in words)]
