import json, os, urllib.request
from collections import Counter
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
USER = 'AnikaJerin'
COLORS = {'Python':'#60a5fa','Jupyter Notebook':'#f59e0b','JavaScript':'#facc15','Go':'#34d399'}
BG = '#07152f'
FG = '#eaf2ff'
MUTED = '#a9bbd8'

# The snapshot is for offline preview. CI fetches current public metadata.
SNAPSHOT = {'total':38, 'classified':{'Python':18,'Jupyter Notebook':9,'JavaScript':2,'Go':1}, 'unclassified':7, 'forks':1, 'years':{'2020':10,'2021':6,'2022':2,'2023':1,'2024':0,'2025':10,'2026':9}}

def live_data():
    repos = []
    headers = {'User-Agent':'anika-profile-chart', 'Accept':'application/vnd.github+json'}
    token = os.getenv('GITHUB_TOKEN')
    if token: headers['Authorization'] = 'Bearer ' + token
    for page in range(1, 10):
        url = f'https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner'
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=25) as response:
            batch = json.load(response)
        repos += batch
        if len(batch) < 100: break
    if not repos: raise RuntimeError('No repositories returned; keeping existing charts')
    original = [r for r in repos if not r['fork']]
    languages = Counter(r['language'] for r in original if r['language'])
    return {'total':len(repos), 'classified':dict(languages), 'unclassified':sum(not r['language'] for r in original), 'forks':len(repos)-len(original), 'years':dict(Counter(r['updated_at'][:4] for r in repos))}

D = SNAPSHOT if os.getenv('OFFLINE_PREVIEW') == '1' else live_data()
(OUT / 'data.json').write_text(json.dumps(D, indent=2) + '\n')

def svg(title, subtitle, body, width=430, height=180):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{escape(title)}</title><desc>{escape(subtitle)}</desc><rect width="{width}" height="{height}" rx="16" fill="{BG}"/><rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="15" fill="none" stroke="#1b3458"/><g font-family="Arial,sans-serif"><text x="20" y="34" font-size="18" font-weight="700" fill="{FG}">{escape(title)}</text><text x="20" y="53" font-size="11" fill="{MUTED}">{escape(subtitle)}</text>{body}</g></svg>'''

def write(name, title, subtitle, body):
    (OUT / name).write_text(svg(title, subtitle, body), encoding='utf-8')

langs = sorted(D['classified'].items(), key=lambda item: -item[1])
known = sum(n for _,n in langs)
# Compact stacked language strip; notebook is a GitHub language label, not a language itself.
parts = ['<clipPath id="b"><rect x="20" y="77" width="390" height="20" rx="7"/></clipPath><g clip-path="url(#b)">']
x = 20
for name,n in langs:
    w = 390*n/known
    parts.append(f'<rect x="{x:.2f}" y="77" width="{w:.2f}" height="20" fill="{COLORS.get(name,"#a78bfa")}"/>')
    x += w
parts.append('</g>')
for i,(name,n) in enumerate(langs[:4]):
    x = 22 + (i%2)*205; y = 123 + (i//2)*29
    parts.append(f'<circle cx="{x}" cy="{y-4}" r="5" fill="{COLORS.get(name,"#a78bfa")}"/><text x="{x+12}" y="{y}" fill="{FG}" font-size="12">{escape(name)} {n}</text>')
write('languages.svg','Programming languages',f'Primary language · {known} non-fork public repos',''.join(parts))

# Counts for the horizontal bar card.
parts=[]
for i,(name,n) in enumerate(langs[:4]):
    y=72+i*25
    parts.append(f'<text x="20" y="{y+10}" fill="{FG}" font-size="11">{escape(name)}</text><rect x="174" y="{y}" width="210" height="11" rx="5" fill="#1b3458"/><rect x="174" y="{y}" width="{210*n/max(1,langs[0][1]):.2f}" height="11" rx="5" fill="{COLORS.get(name,"#a78bfa")}"/><text x="394" y="{y+10}" fill="{FG}" font-size="11">{n}</text>')
write('counts.svg','Repository counts','One primary language per non-fork public repo',''.join(parts))

# Most recently updated year, not repo creation or all activity.
years = sorted(D['years'])
vals = [D['years'][y] for y in years]
points=[]; body=[]
for i,(year,val) in enumerate(zip(years,vals)):
    x=28+i*(370/max(1,len(years)-1)); y=139-65*val/max(1,max(vals))
    points.append((x,y))
    body.append(f'<text x="{x:.1f}" y="158" text-anchor="middle" fill="{MUTED}" font-size="9">{year[2:]}</text>')
body.insert(0, f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in points)}" fill="none" stroke="#60a5fa" stroke-width="2.5"/>')
for (x,y),val in zip(points,vals):
    body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#22d3ee"/><text x="{x:.1f}" y="{y-9:.1f}" text-anchor="middle" fill="{FG}" font-size="11">{val}</text>')
write('updates.svg','Latest update year','Public repos grouped by their most recent update',''.join(body))

# Animated GIF ring: language coverage of original (non-fork) repositories.
covered = known; denominator = known + D['unclassified']
W,H=430,180
font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
regular=ImageFont.truetype(font_path,13); titlefont=ImageFont.truetype(font_path,18); big=ImageFont.truetype(font_path,28)
frames=[]
for frame in range(24):
    im=Image.new('RGB',(W,H),BG); draw=ImageDraw.Draw(im)
    draw.rounded_rectangle((0,0,W-1,H-1),radius=16,outline='#1b3458',width=1)
    draw.text((20,16),'Language coverage',font=titlefont,fill=FG)
    draw.text((20,42),'Public non-fork repositories',font=regular,fill=MUTED)
    box=(31,76,117,162); draw.arc(box,0,359,fill='#254264',width=11)
    draw.arc(box,-90,-90+360*covered/denominator*(frame+1)/24,fill='#22d3ee',width=11)
    draw.text((48,105),f'{covered}/{denominator}',font=regular,fill=FG)
    draw.text((145,84),f'{covered} classified',font=big,fill=FG)
    draw.text((145,124),f'{D["unclassified"]} without a detected language',font=regular,fill=MUTED)
    frames.append(im)
frames[0].save(OUT/'coverage.gif',save_all=True,append_images=frames[1:],duration=55,loop=0,optimize=True)
print('Built four cards:',D)
