#!/usr/bin/env python3
"""Hebrew SRT captions for each tutorial from its own audio (ElevenLabs speech-to-text, word timestamps).

Usage: ELEVENLABS_API_KEY=... python3 tools/make_captions.py [episode ...]
Writes captions/<episode>.srt; existing files are kept unless --force. The key is read from the
environment only and never printed.
"""
import json, os, pathlib, re, subprocess, sys, tempfile, urllib.request, uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
VIDEOS, OUT = ROOT / 'videos', ROOT / 'captions'
BRAND = re.compile(r'\bbe\s*-?\s*easy\s*plus\b|ביאיזי\s*פלוס', re.I)


def transcribe(audio: pathlib.Path):
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in (('model_id', 'scribe_v1'), ('language_code', 'he'), ('timestamps_granularity', 'word'), ('tag_audio_events', 'false')):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode() + audio.read_bytes() + b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode())
    req = urllib.request.Request('https://api.elevenlabs.io/v1/speech-to-text', data=b''.join(parts), method='POST',
                                 headers={'xi-api-key': os.environ['ELEVENLABS_API_KEY'], 'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)


def stamp(seconds):
    ms = int(round(seconds * 1000))
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


def wrap(text, width=42):
    if len(text) <= width:
        return text
    words, best = text.split(), None
    for i in range(1, len(words)):
        a, b = ' '.join(words[:i]), ' '.join(words[i:])
        score = max(len(a), len(b))
        if best is None or score < best[0]:
            best = (score, a, b)
    return f'{best[1]}\n{best[2]}'


def cues(words):
    out, cur = [], []
    for w in words:
        if cur:
            gap = w['start'] - cur[-1]['end']
            text = ' '.join(x['text'] for x in cur)
            if gap > 0.7 or len(text) + len(w['text']) > 80 or w['end'] - cur[0]['start'] > 6.5 or re.search(r'[.?!:]$', cur[-1]['text']):
                out.append(cur); cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return [(c[0]['start'], max(c[-1]['end'], c[0]['start'] + 1.0), BRAND.sub('בי איזי פלוס', ' '.join(x['text'] for x in c))) for c in out]


def build(ep, force=False):
    target = OUT / f'{ep}.srt'
    if target.exists() and not force:
        return 'kept'
    with tempfile.TemporaryDirectory() as tmp:
        audio = pathlib.Path(tmp) / 'a.mp3'
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(VIDEOS / f'{ep}.mp4'), '-vn', '-ac', '1', '-ar', '16000', '-b:a', '48k', str(audio)], check=True)
        result = transcribe(audio)
    words = [w for w in result.get('words', []) if w.get('type') == 'word' and w.get('text', '').strip()]
    items = cues(words)
    for i in range(len(items) - 1):  # never overlap the next cue
        s, e, t = items[i]
        items[i] = (s, min(e + 0.25, items[i + 1][0] - 0.05), t)
    target.write_text(''.join(f'{i}\n{stamp(s)} --> {stamp(e)}\n{wrap(t)}\n\n' for i, (s, e, t) in enumerate(items, 1)), encoding='utf-8')
    return f'{len(items)} cues'


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    force = '--force' in sys.argv
    OUT.mkdir(exist_ok=True)
    eps = args or sorted(p.stem for p in VIDEOS.glob('ep*.mp4')) + sorted(p.stem for p in VIDEOS.glob('beeasy-plus-onboarding-he.mp4'))
    for ep in eps:
        try:
            print(ep, build(ep, force), flush=True)
        except Exception as error:  # keep going; report which episodes need a retry
            print(ep, 'FAILED', type(error).__name__, str(error)[:200], flush=True)
