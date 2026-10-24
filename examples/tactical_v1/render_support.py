from pathlib import Path
import json,os,re
ROOT=Path(__file__).resolve().parent

def speech_engine():
 os.environ['ORT_DISABLE_TELEMETRY']='1'
 import onnxruntime as ort
 from kokoro_onnx import Kokoro
 ort.disable_telemetry_events();options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
 models=ROOT.parent/'.cache/kokoro'
 if not models.exists():models=ROOT/'.cache/kokoro'
 session=ort.InferenceSession(str(models/'kokoro-v1.0.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
 return Kokoro.from_session(session,str(models/'voices-v1.0.bin'))

def phonemes(text,engine):
 names=json.loads((ROOT/'pronunciation.json').read_text())['names']
 names['Protean']='pɹˈoʊtiːən'
 lookup={k.lower():v for k,v in names.items()}
 pattern=re.compile(r'\b('+'|'.join(names)+r")\b(['’]s)?",re.I)
 parts=[];last=0
 for m in pattern.finditer(text):
  if text[last:m.start()].strip():parts.append(engine.tokenizer.phonemize(text[last:m.start()],'en-us'))
  value=lookup[m.group(1).lower()]
  if m.group(2):value+='ɪz' if value[-1] in 'szʃʒʧʤ' else ('s' if value[-1] in 'ptkfθ' else 'z')
  parts.append(value);last=m.end()
 if text[last:].strip():parts.append(engine.tokenizer.phonemize(text[last:],'en-us'))
 result=' '.join(parts)
 unsupported={c for c in result if c not in engine.tokenizer.vocab}
 if unsupported:raise ValueError('Unsupported phonemes: '+repr(unsupported))
 return result
