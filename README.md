# BEEASY PLUS — tutorial videos

Short Hebrew tutorial videos for travel agents, recorded automatically from the
BEEASY PLUS platform on a fictional demo agency (no real customer data).
Files in `videos/` are the source for YouTube uploads.

## Knowledge hub manifest

`site/videos.json` and `site/thumbs/` feed the video library in the BEEASY PLUS
knowledge hub (cached there for an hour). After an upload batch records new
`video_id` values in `metadata/`, run `python3 tools/build_site_manifest.py`
and commit the result.

## Captions and search metadata

- `tools/seo_copy.py` holds the search-first title, opening line and tags per episode;
  `tools/apply_seo.py` rebuilds every metadata description from `description_source`.
  Published videos are updated in bulk by Make scenario 4997227 from `site/youtube_updates.json`.
- `tools/make_captions.py` writes `captions/<episode>.srt` from the video's own audio
  (ElevenLabs speech-to-text, key from the environment only). `tools/caption_batch.py`
  writes `site/caption_uploads.json` for published videos without `captions_uploaded`;
  Make scenario 4997232 uploads them (per-video result in data store 97134,
  key `beeasy_caption_<episode>`).
