from pathlib import Path
from html.parser import HTMLParser
import re, html, shutil, json

ROOT = Path('/home/user/Downloads')
MIRROR = ROOT / 'site_mirror' / 'washvoiceafrica.org'
OUT = ROOT / 'newsite'
ASSETS = OUT / 'assets'
UPLOADS_SRC = MIRROR / 'wp-content' / 'uploads'
UPLOADS_DST = OUT / 'assets' / 'uploads'

ROUTES = [
    '/', '/about-us/', '/services/', '/projects/', '/our-team/', '/contact-us/', '/individual/', '/organization/',
    '/upcoming-events/', '/past-events/', '/video-gallery/', '/symposium/', '/sanitation-accountability-symposium/',
    '/sanitation-pavilion-program-thematic-discussions/', '/annabell-waititu/', '/engr-daniel-k-nganga/',
    '/elizabeth-wambui-mwangi/', '/gallery-2022-sanitation-accountability-webinars/',
    '/gallery-7th-africa-sanitation-conference-6th-11th-november-2023/', '/gallery-sanaccs-report-validation-workshop/',
    '/gallery-sanitation-accountability-symposium/', '/gallery-sanitation-pavilion-in-waspa-international-conference/',
    '/gallery-sectors-stakeholders-meeting-on-water-and-sanitation-act-2023-by-kewasnep-2023/',
    '/gallery-water-and-sanitation-act-2023/', '/feed/', '/comments/feed/'
]

NAV = [
    ('Home','/'),('About','/about-us/'),('Services','/services/'),('Projects','/projects/'),
    ('Team','/our-team/'),('Events','/upcoming-events/'),('Gallery','/video-gallery/'),('Contact','/contact-us/')
]

SUBTITLES = {
    '/': 'Transforming WaSH systems through evidence-based advocacy, inclusive governance, and climate-smart action.',
    '/about-us/': 'Mission, values, and strategic direction for equitable water, sanitation, and hygiene outcomes.',
    '/services/': 'Integrated services spanning communication, capacity building, research, and monitoring.',
    '/projects/': 'Flagship initiatives delivering practical, measurable impact across communities and institutions.',
    '/our-team/': 'Leadership and experts driving policy, partnerships, and implementation excellence.',
    '/contact-us/': 'Connect with WaSHVoice for partnerships, programs, and technical collaboration.',
    '/video-gallery/': 'Field stories, conferences, and thematic discussions in motion.',
}

STRATEGIC_TEXT = (ROOT / 'Strategic_plan_f.txt').read_text(encoding='utf-8', errors='ignore')

class PageExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.capture = False
        self.current_tag = None
        self.buf = []
        self.skip = False
        self.texts = []
        self.imgs = []
        self.links = []
        self.iframes = []
        self.raw = ''

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        ad = dict(attrs)
        if t in {'script', 'style', 'noscript'}:
            self.skip = True
        if t in {'h1','h2','h3','h4','p','li'} and not self.skip:
            self.capture = True
            self.current_tag = t
            self.buf = []
        if t == 'img':
            src = ad.get('src', '').strip()
            if src:
                self.imgs.append(src)
        if t == 'a':
            href = ad.get('href', '').strip()
            if href:
                self.links.append(href)
        if t == 'iframe':
            src = ad.get('src', '').strip()
            if src:
                self.iframes.append(src)
        if t == 'div':
            ds = ad.get('data-settings', '')
            if 'youtube_url' in ds:
                decoded = html.unescape(ds)
                m = re.search(r'"youtube_url":"([^"]+)"', decoded)
                if m:
                    self.iframes.append(m.group(1).replace('\\/', '/'))

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in {'script', 'style', 'noscript'}:
            self.skip = False
        if t in {'h1','h2','h3','h4','p','li'} and self.capture:
            text = ' '.join(''.join(self.buf).split())
            text = html.unescape(text).strip(' -|')
            if len(text) > 22:
                self.texts.append((self.current_tag, text))
            self.capture = False
            self.buf = []

    def handle_data(self, data):
        if self.capture and not self.skip:
            self.buf.append(data)


def rel_prefix(route: str) -> str:
    if route == '/':
        return './'
    depth = len([p for p in route.strip('/').split('/') if p])
    return '../' * depth


def rel_href(prefix: str, u: str) -> str:
    if u == '/':
        return prefix + 'index.html'
    return prefix + u.strip('/') + '/index.html'


def route_to_source(route: str) -> Path:
    if route == '/':
        return MIRROR / 'index.html'
    return MIRROR / route.strip('/') / 'index.html'


def normalize_src(src: str) -> str:
    src = src.strip()
    if not src:
        return ''
    if src.startswith('http://') or src.startswith('https://'):
        if 'washvoiceafrica.org/wp-content/uploads/' in src:
            return '/assets/uploads/' + src.split('/wp-content/uploads/', 1)[1]
        return ''
    src = src.lstrip('./')
    if src.startswith('../'):
        while src.startswith('../'):
            src = src[3:]
    if 'wp-content/uploads/' in src:
        return '/assets/uploads/' + src.split('wp-content/uploads/',1)[1]
    return ''


def to_embed(url: str) -> str:
    if 'youtu.be/' in url:
        vid = url.split('youtu.be/',1)[1].split('?',1)[0]
        return f'https://www.youtube.com/embed/{vid}'
    if 'youtube.com/watch' in url:
        m = re.search(r'[?&]v=([^&]+)', url)
        if m:
            return f'https://www.youtube.com/embed/{m.group(1)}'
    if 'youtube.com/embed/' in url:
        return url
    return url


def curated_texts(texts, limit=14):
    blocked = ['all rights reserved', 'search for:', 'newsletter', 'menu', 'home', 'close', 'read more', 'reply']
    uniq = []
    seen = set()
    for tag, t in texts:
        k = t.lower().strip()
        if any(b in k for b in blocked):
            continue
        if tag in {'h1', 'h2', 'h3', 'h4'} and len(k) < 8:
            continue
        if tag not in {'h1', 'h2', 'h3', 'h4'} and len(k) < 35:
            continue
        if k in seen:
            continue
        seen.add(k)
        uniq.append((tag, t))
    return uniq[:limit]


def strategic_points(max_items=8):
    chunks = [c.strip() for c in re.split(r'(?<=[\.\!\?])\s+', STRATEGIC_TEXT) if len(c.strip()) > 90]
    filtered = []
    for c in chunks:
        if 'WaSHVoice' in c or 'sanitation' in c.lower() or 'Strategic' in c:
            filtered.append(c)
    return filtered[:max_items]


def build_css_js():
    (ASSETS / 'css').mkdir(parents=True, exist_ok=True)
    (ASSETS / 'js').mkdir(parents=True, exist_ok=True)
    css = '''
:root{--ink:#0f172a;--muted:#475569;--c1:#0e7490;--c2:#047857;--surface:#f8fafc}
html{scroll-behavior:smooth}
body{font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--surface);color:var(--ink)}
.gradient{background:radial-gradient(1200px 420px at 15% 0%,rgba(14,116,144,.20),transparent),radial-gradient(900px 360px at 85% 10%,rgba(4,120,87,.18),transparent)}
.glass{backdrop-filter: blur(10px);background:rgba(255,255,255,.78)}
.reveal{opacity:0;transform:translateY(16px);transition:all .55s ease}
.reveal.in{opacity:1;transform:none}
.card{transition:.25s ease transform,.25s ease box-shadow}
.card:hover{transform:translateY(-5px);box-shadow:0 18px 36px rgba(15,23,42,.14)}
.masonry{columns:1;column-gap:1rem}
@media(min-width:768px){.masonry{columns:2}}
@media(min-width:1200px){.masonry{columns:3}}
.masonry-item{break-inside:avoid;margin-bottom:1rem}
.metric{background:linear-gradient(180deg,rgba(255,255,255,.14),rgba(255,255,255,.08));border:1px solid rgba(255,255,255,.18)}
'''
    js = '''
const menuBtn=document.getElementById('menuBtn');
const mobileNav=document.getElementById('mobileNav');
if(menuBtn&&mobileNav){menuBtn.addEventListener('click',()=>mobileNav.classList.toggle('hidden'));}
const io=new IntersectionObserver((entries)=>entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('in')}),{threshold:.12});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
'''
    (ASSETS / 'css' / 'styles.css').write_text(css.strip(), encoding='utf-8')
    (ASSETS / 'js' / 'main.js').write_text(js.strip(), encoding='utf-8')


def ensure_assets():
    (ASSETS / 'images').mkdir(parents=True, exist_ok=True)
    logo = MIRROR / 'wp-content' / 'uploads' / '2023' / '08' / 'logo.png'
    if logo.exists():
        shutil.copy2(logo, ASSETS / 'images' / 'logo.png')
    if UPLOADS_SRC.exists():
        if UPLOADS_DST.exists():
            shutil.rmtree(UPLOADS_DST)
        shutil.copytree(UPLOADS_SRC, UPLOADS_DST)


def make_kpis():
    return [
        ('KES 27B', 'Annual economic drain from sanitation inaction'),
        ('$5.50', 'Target value generated per $1 invested'),
        ('4 Pillars', 'Advocacy, Capacity, Evidence, Climate Resilience'),
        ('2025–2027', 'Strategic implementation window')
    ]


def group_sections(texts):
    sections = []
    current = None
    for tag, text in texts:
        if tag in {'h1', 'h2', 'h3', 'h4'} and len(text) <= 140:
            if current and current['body']:
                sections.append(current)
            current = {'heading': text, 'body': []}
        else:
            if not current:
                current = {'heading': 'Overview', 'body': []}
            current['body'].append(text)
    if current and (current['body'] or current['heading']):
        sections.append(current)

    cleaned = []
    seen = set()
    for section in sections:
        heading = section['heading'].strip()
        body = []
        for paragraph in section['body']:
            key = paragraph.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            body.append(paragraph)
        if body or heading != 'Overview':
            cleaned.append({'heading': heading, 'body': body[:4]})
    return cleaned[:8]


def page_kind(route: str) -> str:
    if route == '/':
        return 'home'
    if route in {'/about-us/', '/individual/', '/organization/'}:
        return 'about'
    if route in {'/annabell-waititu/', '/engr-daniel-k-nganga/', '/elizabeth-wambui-mwangi/', '/our-team/'}:
        return 'team'
    if route in {'/gallery-2022-sanitation-accountability-webinars/', '/gallery-7th-africa-sanitation-conference-6th-11th-november-2023/', '/gallery-sanaccs-report-validation-workshop/', '/gallery-sanitation-accountability-symposium/', '/gallery-sanitation-pavilion-in-waspa-international-conference/', '/gallery-sectors-stakeholders-meeting-on-water-and-sanitation-act-2023-by-kewasnep-2023/', '/gallery-water-and-sanitation-act-2023/'}:
        return 'gallery'
    if route == '/video-gallery/':
        return 'video'
    if route in {'/projects/', '/symposium/', '/upcoming-events/', '/past-events/', '/sanitation-accountability-symposium/', '/sanitation-pavilion-program-thematic-discussions/'}:
        return 'program'
    if route == '/contact-us/':
        return 'contact'
    if route == '/services/':
        return 'services'
    return 'default'


def section_blocks(sections, imgs, prefix):
    blocks = []
    for i, sec in enumerate(sections[:6]):
        bg = 'bg-white' if i % 2 == 0 else 'bg-slate-50'
        img = imgs[i % len(imgs)] if imgs else ''
        img_html = ''
        if img:
            img_html = f'<div class="rounded-2xl overflow-hidden border border-slate-200 shadow-sm reveal"><img src="{prefix}{img.lstrip("/")}" alt="WaSHVoice section visual" class="w-full h-full object-cover min-h-[260px]" loading="lazy" /></div>'

        body = ''.join([f'<p class="text-slate-600 leading-8 mb-4">{html.escape(p)}</p>' for p in sec['body'][:3]])
        if not body:
            body = '<p class="text-slate-600 leading-8 mb-4">This section preserves the original page intent while improving clarity and presentation.</p>'

        text_col = f'''<div class="reveal">
  <div class="inline-flex rounded-full border border-cyan-200 bg-cyan-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-cyan-800 mb-4">Section {i+1}</div>
  <h2 class="text-2xl md:text-3xl font-bold text-slate-900 mb-4">{html.escape(sec['heading'])}</h2>
  {body}
</div>'''

        if img_html:
            content = f'<div class="grid md:grid-cols-2 gap-8 items-center">{text_col}{img_html}</div>' if i % 2 == 0 else f'<div class="grid md:grid-cols-2 gap-8 items-center">{img_html}{text_col}</div>'
        else:
            content = text_col

        blocks.append(f'<section class="{bg}"><div class="max-w-7xl mx-auto px-4 py-14">{content}</div></section>')
    return ''.join(blocks)


def render_page(route: str, data: dict):
    prefix = rel_prefix(route)
    title = data.get('title') or ('WaSHVoice Africa' if route == '/' else route.strip('/').replace('-', ' ').title())
    subtitle = SUBTITLES.get(route, 'Curated content and visual storytelling aligned to WaSHVoice mission and impact.')

    nav_html = ''.join([f'<a href="{rel_href(prefix,u)}" class="text-slate-700 hover:text-cyan-700 font-medium">{n}</a>' for n,u in NAV])
    mob_html = ''.join([f'<a href="{rel_href(prefix,u)}" class="block py-2 text-slate-700">{n}</a>' for n,u in NAV])

    texts = curated_texts(data.get('texts', []), limit=40)
    imgs = data.get('images', [])
    vids = data.get('videos', [])
    kind = page_kind(route)
    sections = group_sections(texts)

    intro_cards = ''.join([
        f'<article class="card rounded-2xl border border-slate-200 bg-white p-6 reveal"><h3 class="font-bold text-slate-900 mb-2">{html.escape(sec["heading"])}</h3><p class="text-slate-600 leading-7">{html.escape((sec["body"][0] if sec["body"] else "This section is optimized from original page content."))}</p></article>'
        for sec in sections[:3]
    ])

    strategic_html = ''
    if route == '/':
        kpis = ''.join([f'<div class="metric rounded-xl p-4"><div class="text-3xl font-extrabold">{k}</div><div class="text-sm mt-1">{d}</div></div>' for k,d in make_kpis()])
        points = ''.join([f'<li class="py-2 border-b border-white/15">{html.escape(p)}</li>' for p in strategic_points(6)])
        strategic_html = f'''
<section class="max-w-7xl mx-auto px-4 py-16">
  <div class="rounded-3xl bg-gradient-to-r from-cyan-700 to-emerald-700 p-8 md:p-12 text-white reveal">
    <h2 class="text-2xl md:text-4xl font-bold">Strategic Plan Highlights</h2>
    <p class="mt-3 text-white/90 max-w-3xl">Integrated strategic priorities from the 2025–2027 plan are embedded into this digital experience to reinforce impact, accountability, and long-term resilience.</p>
    <div class="mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">{kpis}</div>
    <ul class="mt-8 text-sm md:text-base">{points}</ul>
  </div>
</section>'''

    gallery_html = ''
    if imgs:
        items = ''.join([f'<figure class="masonry-item rounded-2xl overflow-hidden bg-white border border-slate-200 reveal"><img src="{prefix}{img.lstrip("/")}" alt="WaSHVoice media" class="w-full h-auto" loading="lazy" /></figure>' for img in imgs[:24]])
        gallery_html = f'''
<section class="max-w-7xl mx-auto px-4 py-14">
  <div class="flex items-end justify-between gap-4 mb-6">
    <h2 class="text-2xl md:text-3xl font-bold text-slate-900">Impact Gallery</h2>
    <p class="text-slate-600 text-sm">Real source media curated from the original website.</p>
  </div>
  <div class="masonry">{items}</div>
</section>'''

    video_html = ''
    if vids:
        embeds = ''.join([
            f'<div class="rounded-2xl overflow-hidden border border-slate-200 bg-white reveal"><iframe class="w-full aspect-video" src="{to_embed(v)}" title="WaSHVoice video" loading="lazy" allowfullscreen></iframe></div>'
            for v in vids[:8]
        ])
        video_html = f'''
<section class="max-w-7xl mx-auto px-4 py-14">
  <h2 class="text-2xl md:text-3xl font-bold text-slate-900 mb-6">Video Stories</h2>
  <div class="grid md:grid-cols-2 gap-6">{embeds}</div>
</section>'''

    timeline_html = ''
    if route in {'/projects/','/symposium/','/upcoming-events/','/past-events/'}:
        timeline_html = '''
<section class="max-w-7xl mx-auto px-4 py-14">
  <h2 class="text-2xl md:text-3xl font-bold text-slate-900 mb-6">Program Flow</h2>
  <div class="grid md:grid-cols-3 gap-5">
    <article class="card rounded-2xl border border-slate-200 bg-white p-6 reveal"><h3 class="font-bold text-slate-900 mb-2">Evidence</h3><p class="text-slate-600">Research-driven diagnostics and mapping guide each intervention.</p></article>
    <article class="card rounded-2xl border border-slate-200 bg-white p-6 reveal"><h3 class="font-bold text-slate-900 mb-2">Co-creation</h3><p class="text-slate-600">Communities, institutions, and partners shape practical implementation.</p></article>
    <article class="card rounded-2xl border border-slate-200 bg-white p-6 reveal"><h3 class="font-bold text-slate-900 mb-2">Scale</h3><p class="text-slate-600">Monitoring and finance models support resilient growth and replication.</p></article>
  </div>
</section>'''

    links_html = ''
    docs = [l for l in data.get('links', []) if '.pdf' in l.lower() or 'strategy' in l.lower()]
    if docs:
        items = ''.join([f'<a href="{d}" target="_blank" class="inline-flex items-center rounded-lg border border-cyan-200 bg-cyan-50 px-4 py-2 text-cyan-800 font-semibold">Open Document</a>' for d in docs[:1]])
        links_html = f'<div class="max-w-7xl mx-auto px-4">{items}</div>'

    structured_html = section_blocks(sections, imgs, prefix)
    if kind == 'services':
        feature_tiles = ''.join([
            f'<article class="card rounded-2xl border border-slate-200 bg-white p-6 reveal"><div class="mb-4 rounded-xl overflow-hidden border border-slate-100">'
            + (f'<img src="{prefix}{imgs[i].lstrip("/")}" class="w-full h-40 object-cover" alt="Service visual" loading="lazy" />' if i < len(imgs) else '<div class="h-40 bg-slate-100"></div>')
            + f'</div><h3 class="text-xl font-semibold text-slate-900 mb-2">{html.escape(sec["heading"])}</h3><p class="text-slate-600">{html.escape((sec["body"][0] if sec["body"] else "Service section optimized from original content."))}</p></article>'
            for i, sec in enumerate(sections[:6])
        ])
        structured_html = f'<section class="max-w-7xl mx-auto px-4 py-14"><h2 class="text-2xl md:text-3xl font-bold text-slate-900 mb-6">Service Areas</h2><div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">{feature_tiles}</div></section>' + structured_html

    if kind == 'team' and imgs:
        profile_intro = f'''<section class="max-w-7xl mx-auto px-4 py-14"><div class="grid md:grid-cols-3 gap-8 items-start"><div class="md:col-span-1 rounded-2xl overflow-hidden border border-slate-200 reveal"><img src="{prefix}{imgs[0].lstrip('/')}" alt="Team profile" class="w-full h-full object-cover" loading="lazy" /></div><div class="md:col-span-2 reveal"><h2 class="text-2xl md:text-3xl font-bold text-slate-900 mb-4">Leadership Profile</h2><p class="text-slate-600 leading-8">{html.escape((sections[0]['body'][0] if sections and sections[0]['body'] else 'Experienced leadership with strategic, technical, and governance expertise in WaSH systems.'))}</p></div></div></section>'''
        structured_html = profile_intro + structured_html

    if kind == 'gallery':
        structured_html = f'<section class="max-w-7xl mx-auto px-4 py-14"><h2 class="text-2xl md:text-3xl font-bold text-slate-900 mb-3">Event Narrative</h2><p class="text-slate-600 max-w-4xl leading-8">{html.escape((sections[0]["body"][0] if sections and sections[0]["body"] else "This gallery section documents stakeholder engagement, learning exchanges, and sector milestones from the original site."))}</p></section>' + structured_html

    html_out = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="WaSHVoice Africa world-class static revamp with curated content, media, and strategic insights." />
  <title>{html.escape(title)} | WaSHVoice Africa</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{prefix}assets/css/styles.css" />
</head>
<body>
  <header class="sticky top-0 z-50 border-b border-slate-200/70 glass">
    <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
      <a href="{prefix}index.html" class="flex items-center gap-3">
        <img src="{prefix}assets/images/logo.png" alt="WaSHVoice logo" class="h-12 w-auto" />
        <span class="font-extrabold text-slate-900 text-lg hidden sm:block">WaSHVoice Africa</span>
      </a>
      <nav class="hidden md:flex items-center gap-6">{nav_html}</nav>
      <button id="menuBtn" class="md:hidden rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold">Menu</button>
    </div>
    <nav id="mobileNav" class="md:hidden hidden border-t border-slate-200 px-4 pb-4">{mob_html}</nav>
  </header>

  <section class="gradient">
    <div class="max-w-7xl mx-auto px-4 py-16 md:py-24">
      <p class="inline-flex rounded-full border border-cyan-200 bg-cyan-50 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cyan-800">Water • Sanitation • Hygiene • Voice</p>
      <h1 class="mt-6 text-4xl md:text-6xl font-extrabold text-slate-900 leading-tight max-w-5xl">{html.escape(title)}</h1>
      <p class="mt-5 text-lg text-slate-700 max-w-3xl">{html.escape(subtitle)}</p>
      <div class="mt-8 flex flex-wrap gap-3">
        <a href="{prefix}projects/index.html" class="rounded-xl bg-cyan-700 px-6 py-3 text-white font-semibold hover:bg-cyan-800 transition">Explore Projects</a>
        <a href="{prefix}contact-us/index.html" class="rounded-xl border border-slate-300 bg-white px-6 py-3 text-slate-800 font-semibold hover:border-cyan-700 hover:text-cyan-700 transition">Partner With Us</a>
      </div>
    </div>
  </section>

  {strategic_html}

    <section class="max-w-7xl mx-auto px-4 py-14">
        <h2 class="text-2xl md:text-3xl font-bold text-slate-900 mb-6">Section Snapshot</h2>
        <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">{intro_cards}</div>
    </section>

    {structured_html}

  {timeline_html}
  {gallery_html}
  {video_html}
  {links_html}

  <footer class="mt-16 bg-slate-950 text-slate-200">
    <div class="max-w-7xl mx-auto px-4 py-12 grid md:grid-cols-3 gap-8">
      <div>
        <img src="{prefix}assets/images/logo.png" alt="WaSHVoice logo" class="h-14 w-auto mb-4" />
        <p class="text-slate-300 leading-7">WaSHVoice strengthens inclusive, climate-resilient, and evidence-driven WaSH systems through advocacy, sector coordination, and strategic partnerships.</p>
      </div>
      <div>
        <h2 class="font-bold text-white mb-3">Quick Links</h2>
        <ul class="space-y-2">
          <li><a href="{prefix}about-us/index.html" class="hover:text-cyan-300">About Us</a></li>
          <li><a href="{prefix}services/index.html" class="hover:text-cyan-300">Services</a></li>
          <li><a href="{prefix}projects/index.html" class="hover:text-cyan-300">Projects</a></li>
          <li><a href="{prefix}video-gallery/index.html" class="hover:text-cyan-300">Video Gallery</a></li>
        </ul>
      </div>
      <div>
        <h2 class="font-bold text-white mb-3">Contact</h2>
        <p class="text-slate-300">Western Heights, Westlands - Nairobi, Kenya</p>
        <p class="text-slate-300">info@washvoiceafrica.org</p>
      </div>
    </div>
    <div class="border-t border-slate-800 py-4 text-center text-sm text-slate-400">© 2026 WaSHVoice Africa. All core source content and media retained and optimized.</div>
  </footer>
  <script src="{prefix}assets/js/main.js"></script>
</body>
</html>'''

    if route == '/':
        dst = OUT / 'index.html'
    else:
        dst = OUT / route.strip('/') / 'index.html'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(html_out, encoding='utf-8')


def collect_data(route: str):
    src = route_to_source(route)
    text_items, images, links, videos = [], [], [], []
    title = None
    if src.exists():
        raw = src.read_text(encoding='utf-8', errors='ignore')
        t = re.search(r'<title>(.*?)</title>', raw, re.I | re.S)
        if t:
            title = html.unescape(re.sub(r'\s+', ' ', t.group(1))).split('&#8211;')[0].strip(' -|')
        parser = PageExtractor()
        parser.feed(raw)
        text_items = parser.texts
        links = parser.links
        videos = []
        for v in parser.iframes:
            vv = html.unescape(v)
            if 'youtube' in vv or 'youtu.be' in vv or 'google.com/maps' in vv:
                videos.append(vv)
        images = []
        for img in parser.imgs:
            n = normalize_src(img)
            if n and n not in images:
                images.append(n)
    return {'title': title, 'texts': text_items, 'images': images, 'links': links, 'videos': videos}


def write_readme():
    readme = '''# WaSHVoice Africa - Static Site (No Server Required)

This folder contains a fully static version of the WaSHVoice Africa website.
It has been optimized to run directly from your file system (by opening `index.html`) or on static hosts like GitHub Pages.

## How to View
1. Open the folder `newsite` on your computer.
2. Double-click `index.html`.
3. Browse the site. All links and images should work without any running server.

## GitHub Pages Deployment
1. Create a new repository on GitHub (e.g., `washvoice-site`).
2. Upload all files from this `newsite` folder to the repository.
3. Go to Settings > Pages > Select `main` branch.
4. The site will be live.

## Features
- **Zero Dependencies**: Pure HTML/CSS/JS.
- **Relative Paths**: Works in any subfolder or local disk.
- **Optimized Assets**: Images and styles included.
'''
    (OUT / 'README.md').write_text(readme, encoding='utf-8')


def main():
    build_css_js()
    ensure_assets()
    for route in ROUTES:
        data = collect_data(route)
        if route == '/':
            data['texts'] = [('p', p) for p in strategic_points(4)] + data['texts']
        render_page(route, data)
    write_readme()
    print('Build complete with uploads copied:', UPLOADS_DST.exists())

if __name__ == '__main__':
    main()
