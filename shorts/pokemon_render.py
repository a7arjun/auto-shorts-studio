"""Original data graphics and procedural attack animation; no franchise assets."""
import json
import math
from pathlib import Path
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageOps
from .pokemon_assets import character_image

W, H, FPS = 720, 1280, 24
BG = '#0a101e'
WHITE = '#f3f5ff'
MUTED = '#a4b1ce'
COLORS = {'Fire':'#ff8951','Water':'#55c7ff','Grass':'#9deb79','Electric':'#ffe373',
          'Ghost':'#bf9aff','Dragon':'#abacff','Normal':'#d5c9b9','Rock':'#ddbd81',
          'Bug':'#b5d96b','Fairy':'#ffb2df','Fighting':'#ff9c97','Dark':'#b9a7c6'}
FONTROOT = Path('/usr/share/fonts/truetype/dejavu')


def font(size, bold=False):
    return ImageFont.truetype(str(FONTROOT/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')), size)


def text(draw, xy, value, size=24, fill=WHITE, bold=False, center=False):
    f=font(size,bold)
    if center:
        width=draw.textbbox((0,0),value,font=f)[2]
        xy=(xy[0]-width/2,xy[1])
    draw.text(xy,value,font=f,fill=fill)


def lines(draw, xy, value, size=24, width=32, fill=WHITE, bold=False, center=False):
    for i,line in enumerate(textwrap.wrap(value,width=width)):
        text(draw,(xy[0],xy[1]+i*(size+9)),line,size,fill,bold,center)


def emblem(draw, x, y, kind, color, radius=44):
    # Abstract elemental markers, deliberately not Pokemon character depictions.
    draw.ellipse((x-radius-12,y-radius-12,x+radius+12,y+radius+12),outline=color,width=2)
    if kind=='Fire':
        points=[(x,y-radius),(x+radius*.35,y-radius*.15),(x+radius*.7,y+radius*.4),
                (x+radius*.4,y+radius),(x-radius*.4,y+radius),(x-radius*.7,y+radius*.3),(x-radius*.2,y-radius*.1)]
        draw.polygon(points,fill=color)
    elif kind=='Water':
        draw.polygon([(x,y-radius),(x-radius*.7,y+radius*.25),(x+radius*.7,y+radius*.25)],fill=color)
        draw.ellipse((x-radius*.7,y-radius*.25,x+radius*.7,y+radius),fill=color)
    elif kind=='Electric':
        draw.polygon([(x+10,y-radius),(x-28,y+5),(x-3,y+5),(x-12,y+radius),(x+30,y-12),(x+4,y-12)],fill=color)
    else:
        draw.regular_polygon((x,y,radius),6,rotation=30,outline=color,width=4)
        text(draw,(x,y-18),kind[:1],28,color,True,True)


def subtitle_chunks(sentence, length=7):
    words=sentence.split()
    return [' '.join(words[i:i+length]) for i in range(0,len(words),length)]


def frame(battle, story, moment):
    image=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(image)
    for yy in range(170,1090,46):
        d.line((28,yy,W-28,yy),fill='#141f35')
    for xx in range(28,W,46):
        d.line((xx,170,xx,1090),fill='#141f35')
    seg=next((s for s in story['segments'] if s['start']<=moment<s['start']+s['duration']),story['segments'][-1])
    local=max(0,moment-seg['start']); progress=min(1,local/max(.01,seg['duration']))
    text(d,(38,32),story['brand'].upper(),21,'#b9adff',True)
    text(d,(500,34),'MATCHUP / 001' if battle['key']=='pilot-v1' else 'MATCHUP / LAB',14,MUTED,False)
    d.line((38,77,682,77),fill='#35425e',width=2)
    text(d,(360,101),'POKEMON BATTLE ANALYSIS',17,MUTED,False,True)
    names=[b['species'] for b in battle['builds']]
    text(d,(360,142),f'{names[0]} vs {names[1]}',32,WHITE,True,True)
    text(d,(360,196),'LEVEL 100  /  BASE FORMS  /  GEN 9 NATIONAL DEX',13,MUTED,False,True)
    event=seg.get('event'); health=seg['health'].copy()
    if event:
        mix=max(0,min(1,(progress-.35)/.3))
        health=[before+(after-before)*mix for before,after in zip(event['before'],event['after'])]
    colors=[COLORS.get(types[0],'#b5a3ff') for types in battle['types']]
    for side,x in enumerate([38,375]):
        color=colors[side]; build=battle['builds'][side]
        d.rounded_rectangle((x,253,x+307,504),radius=22,fill='#152039',outline='#33415d',width=2)
        d.rounded_rectangle((x+17,271,x+290,306),radius=10,fill=color)
        text(d,(x+153,278),' / '.join(battle['types'][side]).upper(),14,'#101624',True,True)
        text(d,(x+153,326),names[side],26,WHITE,True,True)
        text(d,(x+153,369),build['ability'],17,MUTED,False,True)
        text(d,(x+153,400),build['item'],17,MUTED,False,True)
        d.rounded_rectangle((x+20,444,x+287,461),radius=8,fill='#060d19')
        hp=max(0,min(1,health[side]))
        if hp>0:
            d.rounded_rectangle((x+20,444,x+20+267*hp,461),radius=8,fill=color)
        text(d,(x+153,474),f'{round(hp*100)}% HP',15,color,True,True)
    heading=seg['heading']
    lines(d,(360,541),heading,size=28,width=30,bold=True,center=True)
    # Arena markers and travelling energy pulse.
    for side,x in enumerate([164,556]):
        shake=0
        if event and side!=event['actor'] and .55<progress<.7:
            shake=math.sin(moment*85)*7
        y=755+math.sin(moment*2+side)*5
        d.ellipse((x-90,824,x+90,850),fill='#1a2840',outline=colors[side],width=2)
        character=character_image(names[side])
        if character is not None:
            if side==0:
                character=ImageOps.mirror(character)
            image.paste(character,(round(x+shake-character.width/2),round(846-character.height+math.sin(moment*2+side)*5)),character)
        else:
            emblem(d,x+shake,y,battle['types'][side][0],colors[side],48)
    text(d,(360,738),'VS',21,MUTED,True,True)
    if event and .2<progress<.7:
        p=(progress-.2)/.5; actor=event['actor']
        left,right=(164,556) if actor==0 else (556,164)
        x=left+(right-left)*p; y=755-math.sin(p*math.pi)*45
        for radius in [23,15,7]:
            d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=colors[actor])
        if event['miss']:
            text(d,(360,864),'MISSED',20,'#ffd278',True,True)
    if seg['kind']=='rules':
        lines(d,(360,878),'NO MEGA / NO TERA / NO Z-MOVES',16,40,MUTED,center=True)
    elif seg['kind']=='verdict':
        favorite=battle['favorite']
        score=f"{battle['wins'][favorite]} / {battle['trials']} wins" if favorite else 'Even trial results'
        text(d,(360,873),score,27,'#bcacff',True,True)
    elif event:
        text(d,(360,878),f"TURN {event['turn']}  /  REPRESENTATIVE SIMULATION",15,MUTED,False,True)
    speech=seg.get('speech_parts')
    if speech:
        phrase=next((p for p in reversed(speech) if p['start']<=local),speech[0])
        chunks=subtitle_chunks(phrase['text'])
        phrase_progress=max(0,min(.999,(local-phrase['start'])/max(.01,phrase['spoken_duration'])))
        chunk=chunks[min(len(chunks)-1,int(phrase_progress*len(chunks)))]
    else:
        chunks=subtitle_chunks(seg['text'])
        chunk=chunks[min(len(chunks)-1,int(progress*len(chunks)))]
    d.rounded_rectangle((36,963,684,1115),radius=20,fill='#18243c',outline='#354563',width=2)
    lines(d,(360,997),chunk,size=27,width=36,bold=True,center=True)
    text(d,(360,1150),'CONDITIONAL RESULT. BUILDS & RULES IN DESCRIPTION.',13,MUTED,False,True)
    d.rounded_rectangle((38,1200,682,1206),radius=3,fill='#26334b')
    d.rounded_rectangle((38,1200,38+644*min(1,moment/story['duration']),1206),radius=3,fill='#bca7ff')
    text(d,(38,1230),'SIMULATED BATTLE / INDEPENDENT ANALYSIS',12,MUTED)
    return image


def verify_video(path):
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
    video=next(s for s in info['streams'] if s['codec_type']=='video')
    audio=next(s for s in info['streams'] if s['codec_type']=='audio')
    duration=float(info['format']['duration'])
    if not 20<=duration<=90 or video['height']<=video['width'] or audio.get('sample_rate') is None:
        raise ValueError('Video failed duration, portrait or audio checks')
    return {'duration':duration,'width':video['width'],'height':video['height'],'audio':audio['codec_name']}


def render(battle,story,audio,output):
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24',
             '-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','pipe:0','-i',str(audio),
             '-map','0:v','-map','1:a','-c:v','libx264','-preset','veryfast','-crf','21',
             '-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-af','loudnorm=I=-16:TP=-1.5:LRA=9',
             '-movflags','+faststart','-shortest',str(output)]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as process:
        try:
            for i in range(math.ceil(story['duration']*FPS)):
                process.stdin.write(frame(battle,story,i/FPS).tobytes())
        finally:
            process.stdin.close()
            code=process.wait()
        if code:
            raise RuntimeError('FFmpeg render failed')
    frame(battle,story,story['segments'][3]['start']+1).save(output.with_suffix('.png'))
    return verify_video(output)
