"""Pronunciation and pacing independent of script spelling and captions."""
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def lexicon():
    return json.loads((ROOT/'pokemon/pronunciation.json').read_text())


def phonemes_for_text(text, tokenizer, rules=None):
    rules=rules or lexicon()
    entries={**rules['names'],**rules['terms']}
    lookup={name.lower():value for name,value in entries.items()}
    pattern=re.compile(r'\b('+ '|'.join(re.escape(n) for n in sorted(entries,key=len,reverse=True)) + r")\b(['’]s)?",re.IGNORECASE)
    parts=[];start=0
    for match in pattern.finditer(text):
        normal=text[start:match.start()]
        if normal.strip():
            parts.append(tokenizer.phonemize(normal,'en-us'))
        value=lookup[match.group(1).lower()]
        if match.group(2):
            value += 'ɪz' if value[-1] in 'szʃʒʧʤ' else ('s' if value[-1] in 'ptkfθ' else 'z')
        parts.append(value)
        start=match.end()
    if text[start:].strip():
        parts.append(tokenizer.phonemize(text[start:],'en-us'))
    result=' '.join(parts)
    unsupported={c for c in result if c not in tokenizer.vocab}
    if unsupported:
        raise ValueError('Unsupported phonemes: '+repr(unsupported))
    return result


def speech_plan(text, rules=None):
    rules=rules or lexicon()
    builds=json.loads((ROOT/'pokemon/builds.json').read_text())
    # All catalogue attack/item names receive a deliberate post-name pause.
    terms=set(rules['terms'])
    for build in builds:
        terms.add(build['item']);terms.update(build['moves'])
    pattern=re.compile(r'\b(?:'+'|'.join(re.escape(t) for t in sorted(terms,key=len,reverse=True))+r')\b[,;:.!?]?',re.IGNORECASE)
    pieces=[];start=0
    for match in pattern.finditer(text):
        pieces.append({'text':text[start:match.end()].strip(),
                       'pause_after':rules['emphasis_pause_seconds']})
        start=match.end()
    if text[start:].strip():
        pieces.append({'text':text[start:].strip(),'pause_after':rules['segment_pause_seconds']})
    elif pieces:
        pieces[-1]['pause_after']=max(pieces[-1]['pause_after'],rules['segment_pause_seconds'])
    return pieces
