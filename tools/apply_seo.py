#!/usr/bin/env python3
"""Apply tools/seo_copy.py to metadata/*.json (idempotent: always rebuilds from description_source)."""
import json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from seo_copy import SEO, ONBOARDING  # noqa: E402

META = pathlib.Path(__file__).resolve().parent.parent / 'metadata'
BRAND = 'BEEASY PLUS'
BRAND_TAGS = ['BEEASY PLUS', 'בי איזי פלוס', 'מערכת לסוכני נסיעות', 'סוכני נסיעות', 'סוכנות נסיעות']
SITE = 'https://plus.beeasy.pro'


def utm(url, slug):
    base, _, fragment = url.partition('#')
    if base.count('/') == 2:
        base += '/'
    query = f'utm_source=youtube&utm_medium=video&utm_campaign={slug}'
    return f'{base}{"&" if "?" in base else "?"}{query}' + (f'#{fragment}' if fragment else '')


def hashtag(text):
    return '#' + re.sub(r'[^\w]+', '_', text.strip()).strip('_')


def hebrew_body(source, slug, first_tag):
    paragraphs = source.split('\n\n')
    lead = paragraphs[0].replace('בבי איזי פלוס', f'ב־{BRAND}', 1).replace('בי איזי פלוס', f'{BRAND} (בי איזי פלוס)', 1)
    lead = lead.replace('בבי איזי פלוס', f'ב־{BRAND}').replace('לבי איזי פלוס', f'ל־{BRAND}').replace('של בי איזי פלוס', f'של {BRAND}')
    rest = []
    for block in paragraphs[1:]:
        if block.startswith('#'):
            continue
        block = block.replace('להצטרפות לבי איזי פלוס: https://plus.beeasy.pro', f'להצטרפות ל־{BRAND}: {utm(SITE, slug)}')
        block = block.replace('מאגר הידע והמדריכים: https://plus.beeasy.pro/he/knowledge', f'כל המדריכים בעברית: {utm(SITE + "/he/knowledge#videos", slug)}')
        rest.append(block)
    tags_line = ' '.join(dict.fromkeys([hashtag('סוכני נסיעות'), hashtag(first_tag), '#BEEASYPLUS']))
    return [lead, *rest, tags_line]


def main():
    changed = 0
    for path in sorted(META.glob('*.json')):
        slug = path.stem
        if slug not in SEO and slug not in ONBOARDING:
            continue
        data = json.loads(path.read_text())
        source = data.setdefault('description_source', data['description'])
        data.setdefault('title_source', data['title'])
        if slug in SEO:
            title, hook, tags = SEO[slug]
            data['title'] = f'{title} | {BRAND}'
            data['description'] = '\n\n'.join([hook, *hebrew_body(source, slug, tags[0])])
            data['tags'] = ','.join(dict.fromkeys([*tags, *BRAND_TAGS]))
        else:
            title, hook = ONBOARDING[slug]
            data['title'] = title
            body = source.replace('https://plus.beeasy.pro', utm(SITE, slug)).replace('להצטרפות לבי איזי פלוס', f'להצטרפות ל־{BRAND}')
            data['description'] = f'{hook}\n\n{body}'
        assert len(data['title']) <= 100, (slug, len(data['title']))
        assert len(data['description']) <= 5000 and '<' not in data['description'] and '>' not in data['description'], slug
        assert len(data['tags']) <= 480, (slug, len(data['tags']))
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        changed += 1
    print(f'{changed} metadata files updated')


if __name__ == '__main__':
    main()
