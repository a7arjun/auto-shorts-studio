"""CPU-only Kokoro narration. No hosted inference, paid API or cloned voice."""
import hashlib
import os
from pathlib import Path
import time
import urllib.request

MODEL_HASHES = {'kokoro-v1.0.onnx':'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a',
                'voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'}
MODEL_BASE = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'


def download_model(directory=Path('.cache/kokoro')):
    directory.mkdir(parents=True, exist_ok=True)
    for name, minimum in [('kokoro-v1.0.onnx', 100_000_000), ('voices-v1.0.bin', 1_000_000)]:
        target = directory / name
        if target.exists() and target.stat().st_size >= minimum and hashlib.sha256(target.read_bytes()).hexdigest() == MODEL_HASHES[name]:
            continue
        for attempt in range(3):
            try:
                with urllib.request.urlopen(MODEL_BASE + name, timeout=60) as response, open(str(target)+'.part', 'wb') as out:
                    while chunk := response.read(1024 * 1024):
                        out.write(chunk)
                if Path(str(target)+'.part').stat().st_size < minimum or hashlib.sha256(Path(str(target)+'.part').read_bytes()).hexdigest() != MODEL_HASHES[name]:
                    raise RuntimeError('Incomplete voice model download')
                os.replace(str(target)+'.part', target)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
    return directory


def synthesize(story, output, voice='am_michael', speed=1.05):
    # Full process-lifetime telemetry opt-out must precede any ONNX import.
    os.environ['ORT_DISABLE_TELEMETRY'] = '1'
    import numpy as np
    import soundfile as sf
    import onnxruntime as ort
    ort.disable_telemetry_events()
    from kokoro_onnx import Kokoro
    from .pokemon_speech import lexicon, phonemes_for_text, speech_plan
    rules = lexicon()
    directory = download_model()
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(directory/'kokoro-v1.0.onnx'), sess_options=options, providers=['CPUExecutionProvider'])
    engine = Kokoro.from_session(session, str(directory/'voices-v1.0.bin'))
    pieces=[]; start=0
    sample_rate=24000
    for segment in story['segments']:
        phrase_audio=[]; phrase_start=0
        segment['speech_parts']=[]
        for phrase in speech_plan(segment['text'],rules):
            phonemes=phonemes_for_text(phrase['text'],engine.tokenizer,rules)
            audio,sample_rate=engine.create(phonemes,voice=voice,speed=speed,lang='en-us',is_phonemes=True,
                                            sentence_pause=.24,clause_pause=.12)
            duration=len(audio)/sample_rate
            gap=np.zeros(round(sample_rate*phrase['pause_after']),dtype=np.float32)
            segment['speech_parts'].append({**phrase,'start':round(phrase_start,4),
                                            'spoken_duration':round(duration,4),'phonemes':phonemes})
            audio=np.concatenate([audio,gap])
            phrase_start += len(audio)/sample_rate
            phrase_audio.append(audio)
        audio=np.concatenate(phrase_audio)
        segment.update(start=round(start,4),duration=round(len(audio)/sample_rate,4))
        start += len(audio)/sample_rate
        pieces.append(audio)
    sf.write(str(output), np.concatenate(pieces), sample_rate)
    story['duration'] = start
    story['voice'] = {'engine':'kokoro-onnx', 'voice':voice, 'speed':speed, 'pronunciation':'explicit-ipa-v1',
                      'emphasis_pause_seconds':rules['emphasis_pause_seconds'],
                      'model_sha256':hashlib.sha256((directory/'kokoro-v1.0.onnx').read_bytes()).hexdigest()}
    return story
