import json, os, urllib.request
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
OUT.mkdir(exist_ok=True)
USER = 'AnikaJerin'
BG, FG, MUTED = '#151322', '#f5f3ff', '#b6abc8'
COLORS = {'Python':'#aa8cff','Jupyter Notebook':'#ff8b72','JavaScript':'#f9d96c','Go':'#5bd7c7', 'C':'#68ded5', 'C++':'#72a9ff'}
# Public GitHub snapshot on 29 September 2026. The workflow refreshes it with GraphQL.
SNAPSHOT = {'total':38, 'classified':{'Python':18,'Jupyter Notebook':9,'JavaScript':2,'Go':1}, 'language_profile':{'Python':18,'Jupyter Notebook':9,'JavaScript':2,'Go':1,'C':1,'C++':1}, 'unclassified':7, 'forks':1, 'years':{'2020':10,'2021':6,'2022':2,'2023':1,'2024':0,'2025':10,'2026':9}, 'contributions':191, 'commits_2026':38, 'prs':0, 'issues':0, 'current_streak':1, 'longest_streak':4, 'as_of':'29 Sep 2026'}

def request_json(url, payload=None):
    headers = {'User-Agent':'anika-profile-chart', 'Accept':'application/vnd.github+json'}
    token = os.getenv('GITHUB_TOKEN')
    if token: headers['Authorization'] = 'Bearer ' + token
    if payload is not None: headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as response: return json.load(response)

def live_data():
    repos = []
    for page in range(1,10):
        batch = request_json(f'https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner')
        repos += batch
        if len(batch)<100: break
    if not repos: raise RuntimeError('No repositories returned')
    original = [r for r in repos if not r['fork']]
    data = dict(SNAPSHOT)
    data.update(total=len(repos), classified=dict(Counter(r['language'] for r in original if r['language'])), unclassified=sum(not r['language'] for r in original), forks=len(repos)-len(original), years=dict(Counter(r['updated_at'][:4] for r in repos)))
    token = os.getenv('GITHUB_TOKEN')
    if token:
        today = date.today()
        fields = 'totalContributions totalCommitContributions contributionCalendar { weeks { contributionDays { date contributionCount } } }'
        years = range(2020,today.year+1)
        aliases = ' '.join(f'y{y}: contributionsCollection(from:"{y}-01-01T00:00:00Z", to:"{min(date(y,12,31),today).isoformat()}T23:59:59Z") {{ {fields} }}' for y in years)
        query = '{ user(login:"'+USER+'") { '+aliases+' } prs: search(query:"author:'+USER+' is:pr", type:ISSUE) { issueCount } issues: search(query:"author:'+USER+' is:issue", type:ISSUE) { issueCount } }'
        result = request_json('https://api.github.com/graphql', {'query':query})
        if result.get('errors'): raise RuntimeError(result['errors'])
        root = result['data']; collections = root['user']
        data['contributions'] = sum(collections[f'y{y}']['totalContributions'] for y in years)
        data['commits_2026'] = collections.get('y2026',{}).get('totalCommitContributions',0)
        data['prs'],data['issues'] = root['prs']['issueCount'],root['issues']['issueCount']
        days = {d['date']:d['contributionCount'] for y in years for w in collections[f'y{y}']['contributionCalendar']['weeks'] for d in w['contributionDays'] if d['date']<=today.isoformat()}
        run=best=0
        for day in sorted(days):
            run = run+1 if days[day] else 0
            best = max(best,run)
        data['longest_streak']=best
        cursor=today
        if not days.get(cursor.isoformat()): cursor-=timedelta(days=1)
        run=0
        while days.get(cursor.isoformat(),0):
            run+=1; cursor-=timedelta(days=1)
        data['current_streak']=run
        data['as_of']=today.strftime('%d %b %Y').lstrip('0')
    return data

D = SNAPSHOT if os.getenv('OFFLINE_PREVIEW')=='1' else live_data()
(OUT/'data.json').write_text(json.dumps(D,indent=2)+'\n')

def card(name,title,subtitle,body,w=430,h=190):
    out=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>{escape(title)}</title><desc>{escape(subtitle)}</desc><defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#a78bfa" stop-opacity=".48"/><stop offset="1" stop-color="#a78bfa" stop-opacity=".02"/></linearGradient></defs><rect width="{w}" height="{h}" rx="16" fill="{BG}"/><rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="15" fill="none" stroke="#463956"/><g font-family="Arial,sans-serif"><text x="20" y="32" font-size="17" font-weight="700" fill="{FG}">{escape(title)}</text><text x="20" y="50" font-size="11" fill="{MUTED}">{escape(subtitle)}</text>{body}</g></svg>'''
    (OUT/name).write_text(out,encoding='utf-8')

langs=sorted(D['classified'].items(),key=lambda x:-x[1]); known=sum(n for _,n in langs) or 1
# C and C++ are intentionally included in the displayed language profile.  Keep
# this separate from GitHub's primary-language API, which reports only one label
# per repository and otherwise hides those skills.
language_profile=sorted(D.get('language_profile', D['classified']).items(), key=lambda x:-x[1])
profile_total=sum(n for _,n in language_profile) or 1
# Wide card: a filled area plot of the year of latest update for each public repository.
years=sorted(D['years']); values=[D['years'][y] for y in years]
pts=[(366+i*48,145-66*v/max(1,max(values))) for i,v in enumerate(values)]
poly=' '.join(f'{x:.1f},{y:.1f}' for x,y in pts)
area=f'M {pts[0][0]},151 L '+' L '.join(f'{x:.1f},{y:.1f}' for x,y in pts)+f' L {pts[-1][0]},151 Z'
plot=f'<path d="{area}" fill="url(#area)"/><polyline points="{poly}" fill="none" stroke="#ba9aff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
for (x,y),year,val in zip(pts,years,values):
    plot+=f'<circle cx="{x}" cy="{y:.1f}" r="3.5" fill="#68ded5"/><text x="{x}" y="{y-9:.1f}" text-anchor="middle" fill="{FG}" font-size="10">{val}</text><text x="{x}" y="170" text-anchor="middle" fill="{MUTED}" font-size="10">{year[2:]}</text>'
left=''.join(f'<text x="20" y="{y}" fill="{FG}" font-size="12">{escape(t)}</text>' for y,t in [(79,f'◆  {D["total"]} public repositories'),(106,f'◆  {D["contributions"]} total contributions'),(133,'◆  On GitHub since 2020'),(160,f'◆  {D["commits_2026"]} commits in 2026')])
card('stats.svg','AnikaJerin · GitHub snapshot',f'Public activity · as of {D["as_of"]}',left+'<text x="366" y="50" fill="'+MUTED+'" font-size="11">Latest repository update year</text>'+plot,w=700)

# Streak card replaces the old duplicate language mix. Contributions and commits are distinct.
body=f'''<text x="38" y="100" text-anchor="middle" fill="#70ded4" font-size="28" font-weight="700">{D['current_streak']}</text><text x="38" y="122" text-anchor="middle" fill="{MUTED}" font-size="10">current streak</text><text x="144" y="100" text-anchor="middle" fill="#bd9cfa" font-size="28" font-weight="700">{D['longest_streak']}</text><text x="144" y="122" text-anchor="middle" fill="{MUTED}" font-size="10">longest streak</text><text x="247" y="100" text-anchor="middle" fill="#ff9a82" font-size="28" font-weight="700">{D['commits_2026']}</text><text x="247" y="122" text-anchor="middle" fill="{MUTED}" font-size="10">commits · 2026</text><text x="345" y="100" text-anchor="middle" fill="#f3d876" font-size="25" font-weight="700">{D['prs']} / {D['issues']}</text><text x="345" y="122" text-anchor="middle" fill="{MUTED}" font-size="10">PRs / issues</text><path d="M20 142 H410" stroke="#463956"/><text x="215" y="168" text-anchor="middle" fill="{FG}" font-size="11">{D['contributions']} lifetime contributions · through {escape(D['as_of'])}</text>'''
card('activity.svg','Activity & streaks','Public GitHub activity · consecutive contribution days',body)

# Animated donut. Percentages use every displayed language, so they always total 100%.
W,H=430,190
font_path=next((path for path in (
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/System/Library/Fonts/Supplemental/Arial.ttf',
    '/Library/Fonts/Arial.ttf',
) if Path(path).exists()), None)
if not font_path:
    raise RuntimeError('No supported TrueType font found for the language chart')
small=ImageFont.truetype(font_path,10); regular=ImageFont.truetype(font_path,11); titlefont=ImageFont.truetype(font_path,17); big=ImageFont.truetype(font_path,22)
frames=[]
for frame in range(27):
    im=Image.new('RGB',(W,H),BG); draw=ImageDraw.Draw(im)
    draw.rounded_rectangle((0,0,W-1,H-1),radius=16,outline='#463956',width=1)
    draw.text((20,13),'Languages by repository',font=titlefont,fill=FG)
    draw.text((20,40),'Primary label of public non-fork repos',font=regular,fill=MUTED)
    box=(22,66,137,181); draw.arc(box,0,359,fill='#3b304b',width=17)
    angle=-90
    for name,n in language_profile:
        arc=360*n/profile_total*(frame+1)/27
        draw.arc(box,int(angle),int(angle+arc-1),fill=COLORS.get(name,'#a78bfa'),width=17)
        angle+=arc
    draw.text((65,106),'100%',font=big,fill=FG)
    for i,(name,n) in enumerate(language_profile):
        yy=61+i*18; draw.ellipse((157,yy+3,166,yy+12),fill=COLORS.get(name,'#a78bfa'))
        draw.text((175,yy),f'{name}: {100*n/profile_total:.1f}%',font=small,fill=FG)
    draw.text((157,174),'C and C++ included · total = 100%',font=small,fill='#70ded4')
    frames.append(im)
frames[0].save(OUT/'languages.gif',save_all=True,append_images=frames[1:],duration=55,loop=0,optimize=True)

# Recruiter-facing profile signals, deliberately independent of repository counts.
signals=[('Lifetime contributions',D['contributions'],'#aa8cff'),('Commits in 2026',D['commits_2026'],'#ff8b72'),('Longest contribution streak',D['longest_streak'],'#f9d96c'),('Current contribution streak',D['current_streak'],'#5bd7c7')]
signal_max=max(n for _,n,_ in signals) or 1
parts=[]
for i,(label,n,color) in enumerate(signals):
    y=65+i*23
    parts.append(f'<text x="20" y="{y+10}" fill="{FG}" font-size="11">{escape(label)}</text><rect x="191" y="{y}" width="150" height="11" rx="5" fill="#3b304b"/><rect x="191" y="{y}" width="{150*n/signal_max:.1f}" height="11" rx="5" fill="{color}"/><text x="351" y="{y+10}" fill="{FG}" font-size="11">{n}</text>')
parts.append(f'<text x="20" y="169" fill="#70ded4" font-size="11">Public GitHub activity · through {escape(D["as_of"])}</text>')
parts.append(f'<text x="20" y="184" fill="{MUTED}" font-size="9">Profile signals for recruiters — repository listings are available separately.</text>')
card('languages.svg','GitHub profile highlights','Public activity signals for recruiters', ''.join(parts))

# Local image buttons have consistent borders and render on GitHub without CSS support.
for name,label,color,url in [('portfolio','PORTFOLIO','#a78bfa',''),('repositories','REPOSITORIES','#5bd7c7',''),('linkedin','LINKEDIN','#69a8ff','')]:
    w={'portfolio':142,'repositories':173,'linkedin':130}[name]
    img=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="38" viewBox="0 0 {w} 38" role="img"><title>{label}</title><rect x="1" y="1" width="{w-2}" height="36" rx="10" fill="#211a32" stroke="{color}" stroke-width="2"/><circle cx="20" cy="19" r="6" fill="{color}"/><text x="35" y="24" font-family="Arial,sans-serif" font-size="12" font-weight="700" letter-spacing="1" fill="{color}">{label}</text></svg>'''
    (OUT/f'{name}.svg').write_text(img)
print('Built profile cards:',D)
