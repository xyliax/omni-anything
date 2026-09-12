"""Editable paper schematics. Contracts: planning/figure-{1,2}-*.md.

All numbers below define an authored illustration, not a trace replay or a
performance simulation. Events drive block state, capacity totals and ribbons.
"""
from dataclasses import dataclass, field
from pathlib import Path
from html import escape
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'figures'
REVIEW = ROOT / 'build' / 'kv-figure-review'
BLUE, PALE, ORANGE = '#28769B', '#EAF2F7', '#B87519'
INK, GRAY, LIGHT = '#263642', '#9CA9B2', '#E1E7EB'
PERIOD_MS = 1000
OFFSETS_MS = (0, 250, 500, 750)
CAPACITY = 25
SAMPLES_MS = (0, 180, 300, 400, 500, 620, 750, 920, 1100)

class SVG:
    def __init__(self, w, h, title):
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="7in" height="{7*h/w}in" viewBox="0 0 {w} {h}">', f'<title>{escape(title)}</title>', '''<defs>
<pattern id="host" width="5" height="5" patternUnits="userSpaceOnUse"><rect width="5" height="5" fill="#F0F2F4"/><circle cx="2.5" cy="2.5" r=".8" fill="#788A96"/></pattern>
<pattern id="transfer" width="5" height="5" patternUnits="userSpaceOnUse"><rect width="5" height="5" fill="#FFF0D9"/><path d="M-1,1 L1,-1 M0,5 L5,0 M4,6 L6,4" stroke="#B87519" stroke-width="1"/></pattern>
<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#657784"/></marker>
</defs><style>text{font-family:Arial,Helvetica,sans-serif;fill:#263642;font-size:15px}</style>''']
        self.rect(0, 0, w, h, 'white', 'none')
    def rect(self,x,y,w,h,fill='white',stroke=LIGHT,rx=0):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>')
    def text(self,x,y,t,size=15,anchor='start',bold=False,fill=INK):
        self.parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" style="font-size:{size}px;fill:{fill};font-weight:{600 if bold else 400}">{escape(str(t))}</text>')
    def line(self,x,y,xx,yy,color=LIGHT,dash=False,arrow=False,width=1):
        self.parts.append(f'<path d="M{x},{y} L{xx},{yy}" fill="none" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="4 3"' if dash else '')+(' marker-end="url(#arrow)"' if arrow else '')+'/>')
    def diamond(self,x,y):
        self.parts.append(f'<path d="M{x},{y-5} l4,5 l-4,5 l-4,-5 Z" fill="white" stroke="{INK}" stroke-width="1.2"/>')
    def blocks(self,x,y,n,gpu=None,pending=(),host=False,backed=None,storing=(),bw=8,gap=2,bh=9):
        gpu = set(range(n)) if gpu is None else gpu
        for b in range(n):
            valid = b < backed if host and backed is not None else b in gpu
            copying = b in (storing if host else pending)
            fill = 'url(#transfer)' if copying else 'url(#host)' if host and valid else BLUE if valid else 'white'
            self.rect(x+b*(bw+gap),y,bw,bh,fill,ORANGE if copying else GRAY if host or not valid else BLUE)
    def save(self,name):
        p=OUT/(name+'.svg');p.write_text('\n'.join(self.parts+['</svg>']))
        render=shutil.which('rsvg-convert')
        if render:
            subprocess.run([render,'-f','pdf','-o',str(p.with_suffix('.pdf')),str(p)],check=True)
            subprocess.run([render,'-w','1800','-o',str(p.with_suffix('.png')),str(p)],check=True)

@dataclass
class Session:
    n: int = 8
    host: int = 8
    gpu: set = field(default_factory=lambda: {0,1,7})
    pending: set = field(default_factory=set)
    storing: set = field(default_factory=set)
    active: bool = False
    deferred: bool = False

    @property
    def status(self):
        if self.active: return 'Compute'
        if self.pending: return 'Prefetch'
        if self.deferred: return 'Deferred'
        if len(self.gpu)==self.n: return 'Ready'
        return 'Idle'
    @property
    def occupied(self): return len(self.gpu | self.pending)

# Explicit partial-cycle context: S4's preceding execution straddles t=0.
# (start, end) are session execution envelopes, not exclusive GPU kernels.
EXECUTION = {1:[(30,380),(1030,1380)],2:[(280,620)],3:[(530,850)],4:[(-220,120),(780,1120)]}
PREFETCH = {1:[(900,960)],2:[(160,220)],3:[(380,440)],4:[(650,710)]}
# Ordered events resolve ties explicitly: grow/back, idle+evict, then issue.
EVENTS = sorted([
    (20,'back_done',4), (30,'start',1), (120,'evict',4),
    (140,'grow',1), (160,'back_start',1), (160,'issue',2),
    (210,'back_done',1), (220,'complete',2), (280,'start',2),
    (300,'defer',3), (380,'evict',1), (380,'issue',3),
    (420,'grow',2), (440,'complete',3), (450,'back_start',2),
    (490,'back_done',2), (530,'start',3), (600,'grow',3),
    (615,'back_start',3), (620,'evict',2), (650,'issue',4),
    (665,'back_done',3), (710,'complete',4), (780,'start',4),
    (850,'evict',3), (900,'grow',4), (900,'issue',1),
    (915,'back_start',4), (960,'complete',1), (965,'back_done',4),
    (1030,'start',1),
],key=lambda e:(e[0], {'grow':0,'evict':1,'issue':2}.get(e[1],0)))


def snapshot(t):
    ss={i:Session() for i in range(1,5)}
    ss[1].gpu=set(range(8))
    ss[4]=Session(n=9,host=8,gpu=set(range(9)),active=True,storing={8})
    for at,kind,sid in EVENTS:
        if at>t:break
        s=ss[sid]
        if kind=='start':
            assert s.gpu==set(range(s.n)) and not s.pending
            s.active=True
        elif kind=='grow':
            assert s.active
            s.gpu.add(s.n);s.n+=1
        elif kind=='back_start': s.storing=set(range(s.host,s.n))
        elif kind=='back_done': s.host=s.n;s.storing.clear()
        elif kind=='evict':
            assert s.active and s.host==s.n
            s.active=False;s.gpu={0,1,s.n-1}
        elif kind in ('defer','issue'):
            missing=set(range(s.n))-s.gpu
            assert not s.active and not s.pending and all(b<s.host for b in missing)
            fits=sum(x.occupied for x in ss.values())+len(missing)<=CAPACITY
            if kind=='defer':assert not fits;s.deferred=True
            else:
                assert fits and not any(x.pending for x in ss.values())
                s.pending=missing;s.deferred=False
        elif kind=='complete':
            assert s.pending
            s.gpu |= s.pending;s.pending.clear()
        assert sum(x.occupied for x in ss.values())<=CAPACITY
        assert all(not(x.gpu & x.pending) for x in ss.values())
    return ss


def design():
    s=SVG(720,908,'Conveyor: simultaneous KV snapshots, capacity-gated prefetch and staggered releases')
    xs=(116,232,348,464); yy=lambda t:108+.55*t
    s.text(12,24,'T = 1 s   ·   4 release slots',bold=True)
    s.text(708,24,'Illustrative schedule',anchor='end',fill='#647683')
    s.text(17,57,'Time');s.text(19,76,'(ms)')
    for sid,x in enumerate(xs,1):
        s.text(x+47,55,f'S{sid}',bold=True,anchor='middle')
        s.text(x+47,77,f'φ = {OFFSETS_MS[sid-1]}',anchor='middle',fill='#647683')
    s.text(647,55,'GPU pool',anchor='middle',bold=True)
    s.text(647,77,'25 blocks',anchor='middle')
    # Continuous timing remains visible between the simultaneous snapshots.
    s.line(61,yy(0),61,yy(1160),color=GRAY,arrow=True,width=1.5)
    for sid,x in enumerate(xs,1):
        strip=x-10
        s.rect(strip,yy(0),4,yy(1160)-yy(0),'#F1F4F6','none')
        for a,b in EXECUTION[sid]:
            a,b=max(a,0),min(b,1160)
            if b>a:s.rect(strip,yy(a),4,yy(b)-yy(a),BLUE,'none')
        for a,b in PREFETCH[sid]:s.rect(strip,yy(a),4,yy(b)-yy(a),'url(#transfer)',ORANGE)
    for t in SAMPLES_MS:
        cy=yy(t);y=cy-27
        ss=snapshot(t)
        s.line(66,cy,79,cy,GRAY)
        s.text(51,cy+5,t,anchor='end')
        s.text(84,y+33,'G',fill='#647683');s.text(84,y+49,'H',fill='#647683')
        for sid,x in enumerate(xs,1):
            z=ss[sid]
            fill=PALE if z.active else '#FFF7EA' if z.pending or z.deferred else '#F8FAFB'
            s.rect(x-2,y,105,53,fill,ORANGE if z.deferred else LIGHT,3)
            symbol={'Compute':'■','Idle':'·','Prefetch':'↑','Ready':'□','Deferred':'…'}[z.status]
            s.text(x+49,y+18,f'{symbol} {z.status}',anchor='middle',bold=z.active)
            s.blocks(x+2,y+25,z.n,z.gpu,z.pending)
            s.blocks(x+2,y+42,z.n,host=True,backed=z.host,storing=z.storing,bh=7)
            # Mark newly appended blocks until host coverage catches up.
            if z.host<z.n:
                bx=x+2+(z.n-1)*10+4
                s.line(bx-2,y+23,bx+2,y+23,INK);s.line(bx,y+21,bx,y+25,INK)
        total=sum(z.occupied for z in ss.values())
        s.text(647,y+17,f'{total} / {CAPACITY}',anchor='middle',bold=True)
        s.rect(596,y+24,103,8,'white',GRAY)
        s.rect(596,y+24,103*total/CAPACITY,8,PALE,BLUE)
        load=next((sid for sid,z in ss.items() if z.pending),None)
        store=next((sid for sid,z in ss.items() if z.storing),None)
        label=f'↑ S{load}' if load else '↑ —'
        if store:label+=f'   ↓ S{store}'
        s.text(647,y+50,label,anchor='middle',fill=ORANGE if load or store else '#647683')
    # Release markers on ribbons (not snapshot centers or execution boundaries).
    for sid,x in enumerate(xs,1):
        for r in (OFFSETS_MS[sid-1],OFFSETS_MS[sid-1]+PERIOD_MS):
            if r<=1160:s.diamond(x-8,yy(r))
    s.line(14,yy(0),14,yy(1000),GRAY,width=1.2)
    for t in (0,1000):s.line(14,yy(t),24,yy(t),GRAY)
    s.rect(3,yy(500)-12,23,23,'white','none');s.text(14,yy(500)+5,'T',anchor='middle')
    # Causal explanation: a single global gate tied to three visible snapshots.
    s.line(12,752,708,752)
    s.text(12,777,'Capacity → prefetch → reuse',bold=True)
    for x,label,detail in [(12,'300 ms: defer','23 + 5 > 25'),(253,'380 ms: S1 evicts','23 − 6 + 5 = 22'),(516,'440 → 530 ms','S3 ready → compute')]:
        s.text(x,801,label);s.text(x,824,detail,bold=True)
    s.line(175,811,238,811,GRAY,arrow=True)
    s.line(451,811,499,811,GRAY,arrow=True)
    s.rect(12,847,10,10,BLUE,BLUE);s.text(29,858,'GPU KV')
    s.rect(113,847,10,10,'url(#host)',GRAY);s.text(130,858,'Host copy')
    s.rect(228,847,10,10,'url(#transfer)',ORANGE);s.text(246,858,'Copying')
    s.text(337,858,'◇ Release');s.text(442,858,'↑ H2D  ↓ D2H');s.text(592,858,'+ New KV')
    s.text(12,887,'G / H: GPU / Host     □ Ready: idle, KV restored     Pool includes H2D targets',fill='#647683')
    s.save('figure2-design-overview')


def intro():
    s=SVG(720,620,'Periodic KV management: capacity pressure, demand restore and next-use-aware recovery')
    s.text(12,25,'(a)  History grows across updates',bold=True)
    s.text(493,25,'Aggregate full residency',bold=True)
    s.text(88,51,'Earlier',anchor='middle');s.text(303,51,'Later',anchor='middle')
    early=(4,5,4,5);later=(8,8,8,9)
    for sid,(a,b) in enumerate(zip(early,later),1):
        y=65+(sid-1)*23
        s.text(13,y+10,f'S{sid}');s.blocks(52,y,a,bw=10,gap=3,bh=11)
        s.line(132,y+5,194,y+5,GRAY,arrow=True)
        s.blocks(216,y,b,bw=10,gap=3,bh=11)
    # Diagram count, deliberately not a throughput/performance plot.
    bx=502;unit=5.2;capx=bx+CAPACITY*unit
    for y,n in [(79,sum(early)),(123,sum(later))]:
        s.rect(bx,y,35*unit,15,'white',LIGHT)
        s.rect(bx,y,min(n,CAPACITY)*unit,15,PALE,BLUE)
        if n>CAPACITY:s.rect(capx,y,(n-CAPACITY)*unit,15,'#FFF0D9',ORANGE)
        s.text(bx-9,y+13,n,anchor='end')
    s.line(capx,60,capx,151,ORANGE,dash=True,width=1.4)
    s.text(capx,169,'Capacity: 25',anchor='middle')
    s.line(12,187,708,187)
    s.text(12,213,'(b)  Same history, different recovery timing',bold=True)
    s.text(193,243,'Idle KV');s.text(393,243,'Next update of one session')
    tx=lambda t:392+(t+250)*310/750
    release=tx(0)
    rows=[(277,'Full residency','Capacity pressure','keep'),(367,'Demand reload','Restore wait','demand'),(457,'Conveyor','Earlier recovery','prefetch')]
    for y,name,note,mode in rows:
        s.text(12,y,name,bold=True);s.text(12,y+24,note,fill=ORANGE if mode=='demand' else '#647683')
        gpu=set(range(9)) if mode=='keep' else {0,1,8}
        s.text(171,y+1,'G',fill='#647683');s.text(171,y+24,'H',fill='#647683')
        s.blocks(193,y-9,9,gpu,bw=10,gap=3,bh=12)
        s.blocks(193,y+14,9,host=True,backed=9,bw=10,gap=3,bh=9)
        # Thin line = idle retained state; thick band = historical GPU footprint.
        s.rect(tx(-250),y+17,tx(500)-tx(-250),5,PALE,BLUE)
        start_full=-250 if mode=='keep' else 30 if mode=='demand' else -100
        start_compute=90 if mode=='demand' else 30
        end_full=500 if mode=='keep' else start_compute+350
        s.rect(tx(start_full),y+2,tx(end_full)-tx(start_full),20,PALE,BLUE)
        if mode!='keep':
            a,b=(30,90) if mode=='demand' else (-100,-40)
            s.rect(tx(a),y+2,tx(b)-tx(a),20,'url(#transfer)',ORANGE)
            if mode=='demand':
                s.line(tx(a),y+37,tx(b),y+37,ORANGE,width=2)
                s.line(tx(a),y+33,tx(a),y+41,ORANGE);s.line(tx(b),y+33,tx(b),y+41,ORANGE)
            else:
                s.line(tx(-100),y-13,tx(-40),y-13,ORANGE,arrow=True)
        s.rect(tx(start_compute),y+2,tx(start_compute+350)-tx(start_compute),20,BLUE,BLUE)
        s.text((tx(start_compute)+tx(start_compute+350))/2,y+17,'Compute',anchor='middle',fill='white')
        s.line(release,y-17,release,y+28,GRAY,dash=True);s.diamond(release,y-14)
    for t in (-250,0,250,500):
        s.line(tx(t),506,tx(t),511,GRAY);s.text(tx(t),531,str(t),anchor='middle')
    s.line(tx(-250),506,tx(500),506,GRAY)
    s.text(703,553,'Time relative to release (ms)',anchor='end')
    s.text(12,552,'Illustrative blocks and timing',fill='#647683')
    s.line(12,571,708,571)
    s.rect(12,590,11,11,BLUE,BLUE);s.text(31,601,'Compute / GPU KV')
    s.rect(206,590,11,11,PALE,BLUE);s.text(225,601,'Resident, idle')
    s.rect(370,590,11,11,'url(#transfer)',ORANGE);s.text(389,601,'H2D restore')
    s.text(542,601,'◇ Input release')
    s.save('figure1-motivated-example')


def validate_and_export_states():
    # Semantic guards catch incoherent illustration edits before rendering.
    for sid,intervals in EXECUTION.items():
        assert all(0<b-a<PERIOD_MS/2 for a,b in intervals)
    assert snapshot(300)[3].deferred
    assert snapshot(400)[3].pending and snapshot(400)[2].active
    assert snapshot(490)[3].status=='Ready'
    assert snapshot(550)[2].active and snapshot(550)[3].active
    for t in sorted({0,1100,*SAMPLES_MS,*[e[0] for e in EVENTS]}):snapshot(t)
    REVIEW.mkdir(parents=True,exist_ok=True)
    data=[]
    for t in SAMPLES_MS:
        ss=snapshot(t)
        data.append({'time_ms':t,'occupied':sum(s.occupied for s in ss.values()),'sessions':{
            str(i):{'state':s.status,'logical_blocks':s.n,'gpu_valid':sorted(s.gpu),
                    'h2d_destinations':sorted(s.pending),'host_confirmed':s.host,
                    'd2h_destinations':sorted(s.storing),'occupied':s.occupied}
            for i,s in ss.items()}})
    (REVIEW/'snapshot-states.json').write_text(json.dumps(data,indent=2)+'\n')

if __name__=='__main__':
    validate_and_export_states();intro();design()
    try:
        from PIL import Image
        for name in ('figure1-motivated-example','figure2-design-overview'):
            Image.open(OUT/(name+'.png')).convert('L').save(REVIEW/(name+'-gray.png'))
    except ImportError:pass
    print('Rendered authored schematics; validated block accounting, capacity gate and shared H2D schedule.')
