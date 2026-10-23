세금맛집 curated publication

Build: python3 tools/build_site.py
Validate: python3 tools/verify_site.py
Department calculations: python3 -B tools/test_department_analysis.py
Broad directory rebuild: python3 -B tools/broad_seoul.py /path/to/opengov
Broad validation: python3 -B tools/test_broad_seoul.py /path/to/opengov; node tools/test_seoul_directory.cjs
Purpose/address source checks (network): python3 -B tools/audit_meal_semantics.py /path/to/opengov; earlier amount/address checks: python3 -B tools/audit_broad_sources.py
Raw audit: python3 -B tools/audit_departments.py /path/to/opengov

Only the files in this current tree are published. 228 retired regional pages and old catalogue/template snapshots were removed, not hidden using robots/noindex. The build never re-creates them. Retired URLs use the Pages 404 response. tools is excluded by Jekyll.

Nationwide map: data/nationwide-locations.json preserves all 229 regional datasets and 2,186 place entries from the previous curated catalogue. It omits unverified counts, amounts and rankings; saved coordinates are not current business verification. Home and map.html share tools/map_component.py. Leaflet 1.9.4 is vendored with its license; OpenStreetMap provides attributed background tiles.

Place guide: python3 -B tools/place_records.py /path/to/opengov (read-only source; regenerates separate derived files). Test: python3 -B tools/test_place_records.py /path/to/opengov.

Input data: data/place-records.json, data/nationwide-locations.json, data/seoul-2025-evidence.json and data/jeju-observation.json. Field definitions and source restrictions are in method.html and sources.html. Build is deterministic and does not crawl, publish, or run paid generation.
