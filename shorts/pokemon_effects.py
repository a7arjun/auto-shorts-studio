"""Original procedural effects for all 18 move types, with miss/immune paths."""
import math
from PIL import Image, ImageDraw, ImageFilter

TYPE_COLORS={'Normal':'#e2e6ee','Fire':'#ff763b','Water':'#39bcff','Electric':'#ffe44b',
    'Grass':'#8de766','Ice':'#a7edff','Fighting':'#ff9974','Poison':'#cb72ec',
    'Ground':'#d8a567','Flying':'#b6d6ff','Psychic':'#ff84dc','Bug':'#b6db48',
    'Rock':'#d1b78e','Ghost':'#b395ff','Dragon':'#958aff','Dark':'#9a87bb',
    'Steel':'#d1e4f0','Fairy':'#ffb0e5'}


def rgba(color,alpha=255):
    return tuple(int(color[i:i+2],16) for i in (1,3,5))+(int(alpha),)


def star(x,y,r,points=5,spin=0):
    return [(x+math.cos(spin+i*math.pi/points)*r*(1 if i%2==0 else .4),
             y+math.sin(spin+i*math.pi/points)*r*(1 if i%2==0 else .4)) for i in range(points*2)]


def timing(segment,local):
    event=segment.get('event')
    if not event:
        return None,0
    cue=next((p['start'] for p in segment.get('speech_parts',[]) if event['move'].casefold() in p['text'].casefold()),
             segment['duration']*.23)
    phase=(local-cue)/1.65
    hp_mix=max(0,min(1,(phase-.68)/.18))
    return phase,hp_mix


def paint_attack(image,event,phase,start,end):
    if phase is None or not 0<=phase<=1:
        return image
    kind=event.get('move_type')
    if kind not in TYPE_COLORS:
        raise ValueError('Cannot draw an attack without a resolved Pokemon move type')
    layer=Image.new('RGBA',image.size);d=ImageDraw.Draw(layer)
    color=rgba(TYPE_COLORS[kind]);bright=(250,254,255,245)
    fade=min(1,(1-phase)*7)
    color=color[:3]+(int(235*fade),)
    direction=1 if end[0]>start[0] else -1
    p=max(0,min(1,(phase-.12)/.62))
    x=start[0]+(end[0]-start[0])*p
    y=start[1]+(end[1]-start[1])*p
    if event.get('miss'):
        y-=math.sin(p*math.pi/2)*100
    if event.get('immune'):
        p=min(p,.8);x=start[0]+(end[0]-start[0])*p
    travel=phase<.77
    def line(points,width=5,fill=color):d.line(points,fill=fill,width=width,joint='curve')
    def polygon(points,fill=color):d.polygon(points,fill=fill)
    if phase<.14:
        r=12+phase*100
        d.ellipse((start[0]-r,start[1]-r,start[0]+r,start[1]+r),outline=color,width=3)
    if travel:
        tail=x-direction*65
        if kind=='Fire':
            jet='flamethrower' in event['move'].casefold()
            count=40 if jet else 20
            for i in range(count):
                fraction=i/max(1,count-1)
                xx=start[0]+(x-start[0])*fraction if jet else x-direction*(1-fraction)*90
                yy=y+math.sin(phase*31+i*.7)*(5+fraction*5)
                r=5+fraction*15
                d.ellipse((xx-r*1.4,yy-r,xx+r*1.4,yy+r),fill=(255,85,30,230))
                d.ellipse((xx-r,yy-r*.65,xx+r,yy+r*.65),fill=(255,167,45,245))
                d.ellipse((xx-r*.65,yy-r*.3,xx+r*.65,yy+r*.3),fill=(255,241,154,250))
            for i in range(10):
                xx=x-direction*(i*17%max(20,abs(x-start[0])))
                yy=y+math.sin(phase*28+i*2)*(22+i*1.7)
                r=2+i%3
                d.ellipse((xx-r,yy-r*2,xx+r,yy+r*2),fill=(255,177,64,int(225*fade)))
        elif kind=='Water':
            points=[(start[0]+(x-start[0])*i/13,start[1]+(y-start[1])*i/13+math.sin(i*1.1+phase*24)*7) for i in range(14)]
            line(points,16);line([(xx,yy-3) for xx,yy in points],4,bright)
            for i in range(7):
                xx=x-direction*i*13;yy=y+math.sin(i*2+phase*19)*(12+i*2)
                d.ellipse((xx-4,yy-7,xx+4,yy+7),fill=color)
        elif kind=='Electric':
            points=[(start[0]+(x-start[0])*i/11,y+(0 if i in (0,11) else math.sin(i*4+phase*43)*22)) for i in range(12)]
            line(points,9);line(points,3,bright)
            for i in (3,6,8):
                xx,yy=points[i];line([(xx,yy),(xx-direction*9,yy-24),(xx+direction*16,yy-40)],3)
        elif kind=='Grass':
            line([(start[0]+(x-start[0])*i/14,y+math.sin(i*.9+phase*18)*14) for i in range(15)],5)
            for i in range(7):
                xx=x-direction*i*12;yy=y+math.sin(i*2+phase*16)*24
                polygon([(xx-13,yy),(xx+2,yy-8),(xx+14,yy),(xx-2,yy+8)])
                line([(xx-9,yy),(xx+9,yy)],1,bright)
        elif kind=='Ice':
            for i in range(7):
                xx=x-direction*i*12;yy=y+math.sin(i*2)*21
                polygon([(xx-direction*16,yy-9),(xx+direction*23,yy),(xx-direction*12,yy+10)])
                line([(xx-direction*10,yy-4),(xx+direction*17,yy)],2,bright)
        elif kind=='Fighting':
            for i in range(5):line([(tail-direction*i*10,y-26+i*13),(x-direction*5,y-19+i*9)],4)
            polygon(star(x,y,25,7,phase*3));polygon(star(x,y,13,7,phase*3),bright)
        elif kind=='Poison':
            for i in range(6):
                xx=x-direction*i*11;yy=y+math.sin(phase*17+i)*17;r=14-i
                d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=color)
                d.ellipse((xx-r*.5,yy-r*.6,xx,yy),fill=(245,180,255,220))
        elif kind=='Ground':
            for i in range(7):
                xx=x-direction*i*17;yy=y+32+math.sin(i+phase*18)*8
                polygon([(xx-17,yy),(xx-7,yy-22),(xx+9,yy-15),(xx+17,yy+3)])
            line([(tail,y+44),(tail+direction*22,y+35),(x-direction*17,y+49),(x+direction*21,y+34)],3)
        elif kind=='Flying':
            for i in range(4):
                points=[(tail+direction*j*9,y-30+i*18+math.sin(j*.38+phase*20)*10) for j in range(12)]
                line(points,4)
        elif kind=='Psychic':
            for i in range(4):
                xx=x-direction*i*19;r=12+i*4
                d.ellipse((xx-6,y-r,xx+6,y+r),outline=color,width=3)
            line([(tail,y),(x+direction*16,y)],3,bright)
        elif kind=='Bug':
            for i in range(9):
                xx=x-direction*(i%5)*15;yy=y+math.sin(i*3+phase*20)*22
                polygon([(xx+direction*14,yy),(xx-direction*8,yy-4),(xx-direction*8,yy+4)])
        elif kind=='Rock':
            for i in range(5):
                xx=x-direction*i*19;yy=y+math.sin(i*3)*19;r=18-i
                pts=[(xx+math.cos(j*math.pi/3+.3)*r,yy+math.sin(j*math.pi/3+.3)*r) for j in range(6)]
                polygon(pts);line([pts[1],(xx,yy),pts[4]],2,(120,103,83,230))
        elif kind=='Ghost':
            for i in range(6):
                xx=x-direction*i*15;yy=y+math.sin(i+phase*17)*16
                polygon([(xx+direction*17,yy),(xx-direction*5,yy-15),(xx-direction*23,yy-3),
                         (xx-direction*13,yy+5),(xx-direction*20,yy+12),(xx,yy+13)])
        elif kind=='Dragon':
            points=[(tail+direction*i*8,y+math.sin(i*.7-phase*20)*19) for i in range(12)]
            line(points,14);line(points,4,bright)
            polygon([(x+direction*23,y),(x-direction*2,y-16),(x-direction*9,y),(x-direction*2,y+16)])
        elif kind=='Dark':
            for i in range(3):
                xx=x-direction*i*23
                polygon([(xx,y-27),(xx+direction*19,y),(xx,y+27),(xx+direction*6,y),(xx-direction*9,y-10)])
        elif kind=='Steel':
            for i in range(5):
                xx=x-direction*i*15;yy=y+math.sin(i*2)*16
                polygon([(xx-direction*16,yy-5),(xx+direction*23,yy-2),(xx+direction*2,yy+8)])
                line([(xx-direction*12,yy-4),(xx+direction*19,yy-1)],2,bright)
        elif kind=='Fairy':
            for i in range(8):
                xx=x-direction*i*10;yy=y+math.sin(i+phase*14)*24
                polygon(star(xx,yy,10 if i%2 else 15,4,phase*3))
            line([(tail,y),(x,y)],3,(255,218,244,230))
        else:  # Normal: speed streaks and a sharp impact, not a colored ball.
            for i in range(5):line([(tail,y-22+i*11),(x-direction*6,y-18+i*9)],3)
            polygon(star(x,y,24,6,phase*2),bright)
    if phase>=.72 and not event.get('miss') and not event.get('immune'):
        impact=(phase-.72)/.28
        r=(20+impact*52)*(0.7 if event.get('resisted') else 1)
        alpha=int(240*(1-impact));hit=color[:3]+(alpha,)
        polygon(star(end[0],end[1],r,9,phase),hit)
        d.ellipse((end[0]-r*.72,end[1]-r*.72,end[0]+r*.72,end[1]+r*.72),outline=hit,width=3)
        for i in range(9):
            angle=i*2*math.pi/9
            xx=end[0]+math.cos(angle)*r*1.25;yy=end[1]+math.sin(angle)*r*1.25
            d.ellipse((xx-3,yy-3,xx+3,yy+3),fill=hit)
    glow=layer.filter(ImageFilter.GaussianBlur(5))
    base=Image.alpha_composite(image.convert('RGBA'),glow)
    return Image.alpha_composite(base,layer).convert('RGB')
