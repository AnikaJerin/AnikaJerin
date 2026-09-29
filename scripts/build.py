import json, os, urllib.request
from collections import Counter
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
USER = 'AnikaJerin'
COLORS = {'Python':'#a78bfa','Jupyter Notebook':'#ff7a70','JavaScript':'#ffe05c','Go':'#45d6c0'}
BG = '#151322'
FG = '#f5f3ff'
MUTED = '#a6fff2'

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
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{escape(title)}</title><desc>{escape(subtitle)}</desc><rect width="{width}" height="{height}" rx="16" fill="{BG}"/><rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="15" fill="none" stroke="#332847"/><g font-family="Arial,sans-serif"><text x="20" y="34" font-size="18" font-weight="700" fill="{FG}">{escape(title)}</text><text x="20" y="53" font-size="11" fill="{MUTED}">{escape(subtitle)}</text>{body}</g></svg>'''

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
    parts.append(f'<circle cx="{x}" cy="{y-4}" r="5" fill="{COLORS.get(name,"#a78bfa")}"/><text x="{x+12}" y="{y}" fill="{FG}" font-size="12">{escape(name)} {100*n/known:.1f}%</text>')
write('languages.svg','Languages by repository',f'Public non-fork repos · one primary label each' ,''.join(parts))

# Counts for the horizontal bar card.
parts=[]
for i,(name,n) in enumerate(langs[:4]):
    y=72+i*25
    parts.append(f'<text x="20" y="{y+10}" fill="{FG}" font-size="11">{escape(name)}</text><rect x="174" y="{y}" width="210" height="11" rx="5" fill="#342943"/><rect x="174" y="{y}" width="{210*n/max(1,langs[0][1]):.2f}" height="11" rx="5" fill="{COLORS.get(name,"#a78bfa")}"/><text x="394" y="{y+10}" fill="{FG}" font-size="11">{n}</text>')
write('counts.svg','Repository counts','Detected primary language · public non-fork repos',''.join(parts))

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
    body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#45d6c0"/><text x="{x:.1f}" y="{y-9:.1f}" text-anchor="middle" fill="{FG}" font-size="11">{val}</text>')
write('updates.svg','Latest update year','Public repos grouped by their most recent update',''.join(body))

# Animated donut: distribution of detected primary repository labels.
W,H=430,180
font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
regular=ImageFont.truetype(font_path,12); titlefont=ImageFont.truetype(font_path,18); big=ImageFont.truetype(font_path,24)
frames=[]
hex_colors=[COLORS.get(name,'#a78bfa') for name,_ in langs]
for frame in range(25):
    im=Image.new('RGB',(W,H),BG); draw=ImageDraw.Draw(im)
    draw.rounded_rectangle((0,0,W-1,H-1),radius=16,outline='#332847',width=1)
    draw.text((20,15),'Language mix',font=titlefont,fill=FG)
    draw.text((20,40),'30 repos with a detected primary label',font=regular,fill=MUTED)
    box=(27,72,127,172); draw.arc(box,0,359,fill='#342943',width=17)
    angle=-90
    for (name,n), color in zip(langs,hex_colors):
        arc=360*n/known*(frame+1)/25
        draw.arc(box,int(angle),int(angle+arc),fill=color,width=17)
        angle+=arc
    draw.text((53,106),str(known),font=big,fill=FG)
    for i,(name,n) in enumerate(langs[:4]):
        yy=72+i*25
        draw.ellipse((158,yy+4,168,yy+14),fill=hex_colors[i])
        draw.text((180,yy),f'{name}  {100*n/known:.1f}%',font=regular,fill=FG)
    frames.append(im)
frames[0].save(OUT/'languages.gif',save_all=True,append_images=frames[1:],duration=55,loop=0,optimize=True)

# A wide stats + line card modeled on the reference's proportions.
w=680; h=190
left=f'''<text x="20" y="78" fill="{FG}" font-size="13">◈  {D['total']} public repositories</text><text x="20" y="106" fill="{FG}" font-size="13">◈  50 contributions in the last year*</text><text x="20" y="134" fill="{FG}" font-size="13">◈  Active on GitHub since 2020</text><text x="20" y="162" fill="{FG}" font-size="13">◈  7 commits in Sep 2026*</text>'''
years = sorted(D['years']); values=[D['years'][y] for y in years]
pts=[]
for i,(year,val) in enumerate(zip(years,values)):
    xx=322+i*49; yy=144-63*val/max(values)
    pts.append((xx,yy))
chart=f'<polyline points="{" ".join(f"{xx:.0f},{yy:.0f}" for xx,yy in pts)}" fill="none" stroke="#a78bfa" stroke-width="3"/>'
for (xx,yy),year,val in zip(pts,years,values):
    chart+=f'<circle cx="{xx}" cy="{yy:.0f}" r="4" fill="#45d6c0"/><text x="{xx}" y="{yy-10:.0f}" text-anchor="middle" fill="{FG}" font-size="10">{val}</text><text x="{xx}" y="164" text-anchor="middle" fill="{MUTED}" font-size="10">{year[2:]}</text>'
card=f'''<svg xmlns="http://www.w3.org/2000/svg" width="680" height="190" viewBox="0 0 680 190" role="img"><title>GitHub snapshot and last update year</title><rect width="680" height="190" rx="16" fill="''' + BG + '''"/><rect x=".5" y=".5" width="679" height="189" rx="15" fill="none" stroke="#332847"/><g font-family="Arial,sans-serif"><text x="20" y="35" fill="''' + FG + '''" font-size="19" font-weight="700">AnikaJerin · GitHub snapshot</text><text x="322" y="35" fill="''' + MUTED + '''" font-size="12">Latest repo update year · snapshot</text>''' + left + chart + '</g></svg>'
card=card.replace('</g></svg>', f'<text x="20" y="183" fill="{MUTED}" font-family="Arial,sans-serif" font-size="9">*Contributions and Sep commits: Sep 29 snapshot · repository charts refresh weekly</text></g></svg>')
(OUT/'stats.svg').write_text(card)
print('Built four cards:',D)
