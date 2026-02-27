from pathlib import Path
import re, html, shutil
from html.parser import HTMLParser

root = Path('/home/user/Downloads')
mirror = root / 'site_mirror' / 'washvoiceafrica.org'
out = root / 'washvoice-revamp'
assets = out / 'assets'
(assets / 'css').mkdir(parents=True, exist_ok=True)
(assets / 'js').mkdir(parents=True, exist_ok=True)
(assets / 'images').mkdir(parents=True, exist_ok=True)

logo_src = mirror / 'wp-content/uploads/2023/08/logo.png'
if logo_src.exists():
    shutil.copy2(logo_src, assets / 'images/logo.png')

strategic = (root / 'Strategic_plan_f.txt').read_text(encoding='utf-8', errors='ignore')

def strategic_blurbs(n=4):
    chunks = [c.strip() for c in re.split(r'(?<=[\.\!\?])\s+', strategic) if len(c.strip()) > 80]
    return chunks[:n]

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.capture=False
        self.buf=[]
        self.items=[]
        self.skip=False
    def handle_starttag(self, tag, attrs):
        t=tag.lower()
        if t in {'script','style','noscript'}:
            self.skip=True
        if t in {'h1','h2','h3','h4','p','li'} and not self.skip:
            self.capture=True
            self.buf=[]
            self.curr=t
    def handle_endtag(self, tag):
        t=tag.lower()
        if t in {'script','style','noscript'}:
            self.skip=False
        if t in {'h1','h2','h3','h4','p','li'} and self.capture:
            txt=' '.join(''.join(self.buf).split())
            txt=html.unescape(re.sub(r'\s+',' ',txt)).strip(' -|')
            if txt and len(txt) > 20 and 'cookie' not in txt.lower():
                self.items.append((self.curr, txt))
            self.capture=False
            self.buf=[]
    def handle_data(self, data):
        if self.capture and not self.skip:
            self.buf.append(data)

def extract_content(path: Path):
    if not path.exists():
        return []
    raw = path.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'<main[\s\S]*?</main>', raw, re.I)
    section = m.group(0) if m else re.search(r'<body[\s\S]*?</body>', raw, re.I)
    raw2 = section.group(0) if section else raw
    parser = TextExtractor(); parser.feed(raw2)
    seen=set(); out_items=[]
    for tag,text in parser.items:
        key=text.lower()
        if key in seen: continue
        seen.add(key)
        if any(bad in key for bad in ['subscribe to our newsletter','search for:','all rights reserved']):
            continue
        out_items.append((tag,text))
    return out_items[:28]

routes = [
    '/', '/about-us/', '/services/', '/projects/', '/our-team/', '/contact-us/', '/individual/', '/organization/',
    '/upcoming-events/', '/past-events/', '/video-gallery/', '/symposium/', '/sanitation-accountability-symposium/',
    '/sanitation-pavilion-program-thematic-discussions/', '/annabell-waititu/', '/engr-daniel-k-nganga/',
    '/elizabeth-wambui-mwangi/', '/gallery-2022-sanitation-accountability-webinars/',
    '/gallery-7th-africa-sanitation-conference-6th-11th-november-2023/', '/gallery-sanaccs-report-validation-workshop/',
    '/gallery-sanitation-accountability-symposium/', '/gallery-sanitation-pavilion-in-waspa-international-conference/',
    '/gallery-sectors-stakeholders-meeting-on-water-and-sanitation-act-2023-by-kewasnep-2023/',
    '/gallery-water-and-sanitation-act-2023/', '/feed/', '/comments/feed/'
]

nav = [
    ('Home','/'),('About','/about-us/'),('Services','/services/'),('Projects','/projects/'),
    ('Team','/our-team/'),('Events','/upcoming-events/'),('Gallery','/video-gallery/'),('Contact','/contact-us/')
]

page_subtitles = {
    '/': 'Evidence-based advocacy and climate-smart action for inclusive WaSH systems across Africa.',
    '/about-us/':'Who we are, what we stand for, and how we bridge policy and people.',
    '/services/':'Core capabilities supporting resilient, just, and data-driven WaSH outcomes.',
    '/projects/':'Programs and initiatives delivering measurable sanitation and hygiene impact.',
    '/our-team/':'Meet the professionals leading strategy, partnerships, and implementation.',
    '/contact-us/':'Partner with WaSHVoice or request information from our team.',
}

(assets / 'css' / 'styles.css').write_text("""
:root{--brand-50:#ecfeff;--brand-100:#cffafe;--brand-600:#0891b2;--brand-700:#0e7490;--emerald-700:#047857;--ink:#0f172a}
html{scroll-behavior:smooth}
body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#f8fafc;color:#0f172a}
.hero-grid{background-image:radial-gradient(circle at 20% 20%, rgba(8,145,178,.22), transparent 35%),radial-gradient(circle at 80% 0%, rgba(4,120,87,.16), transparent 30%)}
.glass{backdrop-filter: blur(8px); background: rgba(255,255,255,.75)}
.reveal{opacity:0;transform:translateY(18px);transition:all .6s ease}
.reveal.in{opacity:1;transform:translateY(0)}
.card{transition:transform .25s ease, box-shadow .25s ease}
.card:hover{transform:translateY(-4px);box-shadow:0 18px 30px rgba(2,6,23,.12)}
""".strip(), encoding='utf-8')

(assets / 'js' / 'main.js').write_text("""
const btn=document.getElementById('menuBtn');
const mobile=document.getElementById('mobileNav');
if(btn&&mobile){btn.addEventListener('click',()=>mobile.classList.toggle('hidden'));}
const io=new IntersectionObserver((entries)=>{entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('in')})},{threshold:.12});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
""".strip(), encoding='utf-8')


def rel_prefix(route):
    if route == '/':
        return './'
    depth = len([p for p in route.strip('/').split('/') if p])
    return '../' * depth

def rel_href(prefix, u):
    if u == '/':
        return prefix
    return prefix + u.strip('/') + '/'

for route in routes:
    route_clean = route.strip('/')
    src = mirror / ('index.html' if route=='/' else f'{route_clean}/index.html')
    items = extract_content(src)
    title = 'WaSHVoice'
    if items and items[0][0].startswith('h'):
        title = items[0][1]
    elif route != '/':
        title = route_clean.replace('-', ' ').title()

    prefix = rel_prefix(route)
    nav_html=''.join([f'<a href="{rel_href(prefix,u)}" class="text-slate-700 hover:text-cyan-700 font-medium">{n}</a>' for n,u in nav])
    mobile_nav=''.join([f'<a href="{rel_href(prefix,u)}" class="block py-2 text-slate-700">{n}</a>' for n,u in nav])

    cards=''
    use_items = items[:12]
    if route == '/':
        for s in strategic_blurbs(4):
            cards += f'<article class="card rounded-2xl border border-cyan-100 bg-white p-6 reveal"><p class="text-slate-700 leading-7">{html.escape(s)}</p></article>'
    for tag,text in use_items:
        if len(text) < 35:
            continue
        if tag.startswith('h'):
            cards += f'<article class="card rounded-2xl border border-slate-200 bg-white p-6 reveal"><h3 class="text-lg font-semibold text-slate-900 mb-2">{html.escape(text[:80])}</h3><p class="text-slate-600 leading-7">{html.escape(text)}</p></article>'
        else:
            cards += f'<article class="card rounded-2xl border border-slate-200 bg-white p-6 reveal"><p class="text-slate-700 leading-7">{html.escape(text)}</p></article>'

    if not cards:
        cards = '<article class="rounded-2xl border border-slate-200 bg-white p-6 reveal"><p class="text-slate-700 leading-7">Content from the original WaSHVoice page is being optimized for this section while preserving purpose and message.</p></article>'

    subtitle = page_subtitles.get(route, 'Optimized content and modern user experience aligned with WaSHVoice mission and impact.')

    cta = ''
    if route == '/':
        cta = '''
<section class="max-w-6xl mx-auto px-4 py-16">
  <div class="rounded-3xl bg-gradient-to-r from-cyan-700 to-emerald-700 p-8 md:p-12 text-white reveal">
    <h2 class="text-2xl md:text-4xl font-bold mb-4">Strategic Direction 2025–2027</h2>
    <p class="opacity-95 leading-7 max-w-3xl">WaSHVoice advances four pillars: Advocacy & Justice, Capacity Building, Research & Evidence, and Climate Resilience. The roadmap targets measurable economic and social returns through data-informed and community-centered action.</p>
    <div class="mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="rounded-xl bg-white/15 p-4"><div class="text-3xl font-extrabold">$5.50</div><div class="text-sm mt-1">Target value created per $1 invested</div></div>
      <div class="rounded-xl bg-white/15 p-4"><div class="text-3xl font-extrabold">2025</div><div class="text-sm mt-1">National Sanitation Directory foundation year</div></div>
      <div class="rounded-xl bg-white/15 p-4"><div class="text-3xl font-extrabold">2026</div><div class="text-sm mt-1">Professional standards and entrepreneurship hub</div></div>
      <div class="rounded-xl bg-white/15 p-4"><div class="text-3xl font-extrabold">2027</div><div class="text-sm mt-1">Scale blended finance and NSD 2.0</div></div>
    </div>
  </div>
</section>'''

    html_out = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="WaSHVoice Africa - modernized static website revamp focused on advocacy, equity, and resilient WaSH systems." />
  <title>{html.escape(title)} | WaSHVoice Africa</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{prefix}assets/css/styles.css" />
</head>
<body>
  <header class="sticky top-0 z-50 border-b border-slate-200/70 glass">
    <div class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
      <a href="{prefix}" class="flex items-center gap-3">
        <img src="{prefix}assets/images/logo.png" alt="WaSHVoice logo" class="h-12 w-auto" />
        <span class="font-extrabold text-slate-900 text-lg hidden sm:block">WaSHVoice Africa</span>
      </a>
      <nav class="hidden md:flex items-center gap-6">{nav_html}</nav>
      <button id="menuBtn" class="md:hidden rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold">Menu</button>
    </div>
    <nav id="mobileNav" class="md:hidden hidden border-t border-slate-200 px-4 pb-4">{mobile_nav}</nav>
  </header>

  <section class="hero-grid">
    <div class="max-w-6xl mx-auto px-4 py-16 md:py-24">
      <p class="inline-flex rounded-full border border-cyan-200 bg-cyan-50 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cyan-800">Water • Sanitation • Hygiene • Voice</p>
      <h1 class="mt-6 text-4xl md:text-6xl font-extrabold text-slate-900 leading-tight max-w-4xl">{html.escape(title)}</h1>
      <p class="mt-6 text-lg text-slate-700 max-w-3xl">{html.escape(subtitle)}</p>
      <div class="mt-8 flex flex-wrap gap-3">
        <a href="{prefix}projects/" class="rounded-xl bg-cyan-700 px-6 py-3 text-white font-semibold hover:bg-cyan-800 transition">Explore Projects</a>
        <a href="{prefix}contact-us/" class="rounded-xl border border-slate-300 bg-white px-6 py-3 text-slate-800 font-semibold hover:border-cyan-700 hover:text-cyan-700 transition">Partner With Us</a>
      </div>
    </div>
  </section>

  {cta}

  <main class="max-w-6xl mx-auto px-4 py-14">
    <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">{cards}</div>
  </main>

  <footer class="mt-16 bg-slate-950 text-slate-200">
    <div class="max-w-6xl mx-auto px-4 py-12 grid md:grid-cols-3 gap-8">
      <div>
        <img src="{prefix}assets/images/logo.png" alt="WaSHVoice logo" class="h-14 w-auto mb-4" />
        <p class="text-slate-300 leading-7">WaSHVoice strengthens inclusive, climate-resilient, and evidence-driven WaSH systems through advocacy, coordination, and strategic partnerships.</p>
      </div>
      <div>
        <h2 class="font-bold text-white mb-3">Quick Links</h2>
        <ul class="space-y-2">
          <li><a href="{prefix}about-us/" class="hover:text-cyan-300">About Us</a></li>
          <li><a href="{prefix}services/" class="hover:text-cyan-300">Services</a></li>
          <li><a href="{prefix}projects/" class="hover:text-cyan-300">Projects</a></li>
          <li><a href="{prefix}our-team/" class="hover:text-cyan-300">Our Team</a></li>
        </ul>
      </div>
      <div>
        <h2 class="font-bold text-white mb-3">Contact</h2>
        <p class="text-slate-300">Nairobi, Kenya</p>
        <p class="text-slate-300">info@washvoiceafrica.org</p>
        <p class="text-slate-300">+254 700 000 000</p>
      </div>
    </div>
    <div class="border-t border-slate-800 py-4 text-center text-sm text-slate-400">© 2026 WaSHVoice Africa. Revamped static UI preserving original content intent.</div>
  </footer>

  <script src="{prefix}assets/js/main.js"></script>
</body>
</html>'''

    if route == '/':
        dest = out / 'index.html'
    else:
        dest = out / route_clean / 'index.html'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html_out, encoding='utf-8')

(out / 'README.md').write_text('''# WaSHVoice Africa Static Revamp

Modern static revamp of the original WaSHVoice site using HTML + Tailwind CSS + vanilla JavaScript.

## What is included
- Preserved route structure for mirrored public pages
- Shared responsive layout and navigation
- Optimized, readable content cards extracted from the original pages
- Strategic context sections sourced from `Strategic_plan_f.txt`
- Subtle reveal animations and mobile navigation

## Run locally

```bash
cd washvoice-revamp
python3 -m http.server 8080
```

Open `http://localhost:8080`.

## Validate routes

```bash
python3 scripts/validate_routes.py
```
''', encoding='utf-8')

(out / 'package.json').write_text('''{
  "name": "washvoice-revamp-static",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "serve": "python3 -m http.server 8080",
    "check": "python3 scripts/validate_routes.py"
  }
}
''', encoding='utf-8')

(out / 'scripts').mkdir(exist_ok=True)
(out / 'scripts/validate_routes.py').write_text('''from pathlib import Path

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
''', encoding='utf-8')

print('Generated at', out)
