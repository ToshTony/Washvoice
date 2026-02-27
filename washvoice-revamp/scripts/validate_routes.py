from pathlib import Path

root = Path(__file__).resolve().parents[1]
routes = [
    'index.html','about-us/index.html','services/index.html','projects/index.html','our-team/index.html','contact-us/index.html',
    'individual/index.html','organization/index.html','upcoming-events/index.html','past-events/index.html','video-gallery/index.html',
    'symposium/index.html','sanitation-accountability-symposium/index.html','sanitation-pavilion-program-thematic-discussions/index.html',
    'annabell-waititu/index.html','engr-daniel-k-nganga/index.html','elizabeth-wambui-mwangi/index.html',
    'gallery-2022-sanitation-accountability-webinars/index.html','gallery-7th-africa-sanitation-conference-6th-11th-november-2023/index.html',
    'gallery-sanaccs-report-validation-workshop/index.html','gallery-sanitation-accountability-symposium/index.html',
    'gallery-sanitation-pavilion-in-waspa-international-conference/index.html',
    'gallery-sectors-stakeholders-meeting-on-water-and-sanitation-act-2023-by-kewasnep-2023/index.html',
    'gallery-water-and-sanitation-act-2023/index.html','feed/index.html','comments/feed/index.html'
]
missing = [r for r in routes if not (root / r).exists()]
if missing:
    print('Missing routes:')
    for m in missing:
        print('-', m)
    raise SystemExit(1)
print(f'OK: {len(routes)} routes present')
