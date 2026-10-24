#!/usr/bin/env python3
"""Build site/videos.json and small site/thumbs/*.jpg for the BEEASY PLUS knowledge hub.

The site reads site/videos.json (cached for an hour), so a video appears there as soon as
its metadata has a video_id and this script has run. Run after every upload batch.
"""
import json, pathlib, re, subprocess, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
META, THUMBS, SITE = ROOT / 'metadata', ROOT / 'thumbs', ROOT / 'site'
STAMP = re.compile(r'^(\d+):(\d{2})\s+(.+)$')


def chapters(description):
    lines = description.split('פרקים:', 1)[1].strip().splitlines() if 'פרקים:' in description else []
    out = []
    for line in lines:
        m = STAMP.match(line.strip())
        if not m:
            break
        out.append([int(m[1]) * 60 + int(m[2]), m[3].strip()])
    return out


def main():
    (SITE / 'thumbs').mkdir(parents=True, exist_ok=True)
    videos = {}
    for path in sorted(META.glob('*.json')):
        if path.stem in ('upload_queue', 'channel'):
            continue
        data = json.loads(path.read_text())
        vid = data.get('video_id')
        if not vid or vid == 'TBD':
            continue
        src, thumb = THUMBS / f'{path.stem}.png', SITE / 'thumbs' / f'{path.stem}.jpg'
        if src.exists() and (not thumb.exists() or thumb.stat().st_mtime < src.stat().st_mtime):
            subprocess.run(['convert', str(src), '-resize', '640x360', '-strip', '-quality', '78', str(thumb)], check=True)
        videos[path.stem] = {'id': vid, 'title': data.get('title', ''), 'chapters': chapters(data.get('description', '')), 'thumb': thumb.exists()}
    manifest = {'updated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'videos': videos}
    (SITE / 'videos.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n')
    print(f'{len(videos)} videos in site/videos.json')


if __name__ == '__main__':
    main()
