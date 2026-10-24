# BEEASY PLUS — tutorial videos

Short Hebrew tutorial videos for travel agents, recorded automatically from the
BEEASY PLUS platform on a fictional demo agency (no real customer data).
Files in `videos/` are the source for YouTube uploads.

## Knowledge hub manifest

`site/videos.json` and `site/thumbs/` feed the video library in the BEEASY PLUS
knowledge hub (cached there for an hour). After an upload batch records new
`video_id` values in `metadata/`, run `python3 tools/build_site_manifest.py`
and commit the result.
