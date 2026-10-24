#!/usr/bin/env python3
"""Build site/caption_uploads.json: one multipart captions.insert body per published video that has
captions/<episode>.srt and is not yet marked captions_uploaded. Usage: caption_batch.py [episode ...] [--out file]"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
B = 'beeasycaptionboundary'


LANGS = {'he': ('iw', 'עברית'), 'en': ('en', 'English'), 'ru': ('ru', 'Русский'), 'ar': ('ar', 'العربية')}


def body(video_id, srt, lang='he'):
    code, name = LANGS[lang]
    meta = json.dumps({'snippet': {'videoId': video_id, 'language': code, 'name': name, 'isDraft': False}}, ensure_ascii=False)
    return f'--{B}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n--{B}\r\nContent-Type: application/octet-stream\r\n\r\n{srt}\r\n--{B}--\r\n'


args = [a for a in sys.argv[1:] if not a.startswith('--')]
out = ROOT / 'site' / 'caption_uploads.json'
if '--out' in sys.argv:
    out = pathlib.Path(sys.argv[sys.argv.index('--out') + 1]); args = [a for a in args if a != str(out)]
rows = []
for path in sorted((ROOT / 'metadata').glob('*.json')):
    ep = path.stem
    if args and ep not in args:
        continue
    data = json.loads(path.read_text())
    srt = ROOT / 'captions' / f'{ep}.srt'
    if data.get('video_id') in (None, 'TBD') or data.get('captions_uploaded') or not srt.exists():
        continue
    lang = ep.rsplit('-', 1)[-1] if ep.startswith('beeasy-plus-onboarding-') else 'he'
    rows.append({'ep': ep, 'id': data['video_id'], 'body': body(data['video_id'], srt.read_text(encoding='utf-8'), lang)})
out.write_text(json.dumps(rows, ensure_ascii=False) + '\n')
print(len(rows), 'caption uploads in', out.name)
