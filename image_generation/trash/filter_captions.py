import re, pandas as pd
import spacy
nlp = spacy.load("en_core_web_sm", disable=["ner","parser","textcat"])

def build_regex(words):
    esc = [re.escape(w) for w in words]
    # word-boundary for single tokens; fall back to plain for multiword phrases
    wb = [fr"\b{w}\b" if " " not in w else w for w in esc]
    return re.compile("|".join(wb), re.I)

def caption_tokens(c):
    # simple fallback tokenizer; for object-specific length_max a simple split is ok
    return re.findall(r"[A-Za-z0-9']+", c.lower())

def lemmatize(text):
    doc = nlp(text)
    return " ".join([t.lemma_.lower() for t in doc])

class Rule:
    def __init__(self, name, cfg):
        self.name = name
        self.heads = cfg["head"]
        self.re_head = build_regex([h for h in self.heads if " " not in h])
        self.positive_templates = [s.lower() for s in cfg.get("positive_templates",[])]
        self.re_pos_templates = build_regex(self.positive_templates) if self.positive_templates else None
        self.positive_tokens = set([s.lower() for s in cfg.get("positive_tokens",[])])
        self.negative_exact = [s.lower() for s in cfg.get("negative_exact",[])]
        self.re_neg_exact = build_regex(self.negative_exact) if self.negative_exact else None
        self.negative_tokens = set([s.lower() for s in cfg.get("negative_tokens",[])])
        self.multi_object_tokens = set([s.lower() for s in cfg.get("multi_object_tokens",[])])
        self.length_max = cfg.get("length_max", 15)

    def accept(self, caption):
        cap = caption.strip().lower()
        toks = caption_tokens(cap)
        if len(toks) > self.length_max:
            return False, "len"
        if self.re_neg_exact and self.re_neg_exact.search(cap):
            return False, "neg_exact"

        # quick token-set checks
        tokset = set(toks)
        if tokset & self.multi_object_tokens:
            return False, "multi"

        # positive template hit?
        if self.re_pos_templates and self.re_pos_templates.search(cap):
            pos_hit = True
        else:
            # head presence using lemma to catch plurals
            lem = lemmatize(cap)
            if not any(re.search(fr"\b{re.escape(h)}\b", lem) for h in self.heads):
                return False, "no_head"
            pos_hit = len(tokset & self.positive_tokens) > 0

        if not pos_hit:
            return False, "no_pos"

        # negative tokens kill
        if tokset & self.negative_tokens:
            return False, "neg_tok"

        # extra: forbid “and/with …” patterns for clutter
        if re.search(r"\b(and|with|surrounded by|next to|near)\b", cap):
            return False, "clutter_phrase"

        return True, "ok"
