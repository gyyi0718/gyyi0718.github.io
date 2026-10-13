세금맛집 curated publication

Build: python3 tools/build_site.py
Validate: python3 tools/verify_site.py

Only the files in this current tree are published. 228 retired regional pages and old catalogue/template snapshots were removed, not hidden using robots/noindex. The build never re-creates them. Retired URLs use the Pages 404 response. tools is excluded by Jekyll.

Input data: data/seoul-2025-evidence.json and data/jeju-observation.json. Field definitions and source restrictions are in method.html and sources.html. Build is deterministic and does not crawl, publish, or run paid generation.
