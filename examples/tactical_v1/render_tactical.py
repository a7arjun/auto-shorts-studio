"""One mechanics-backed tactical example; renders only and never uploads."""
from pathlib import Path
import json,math,os,subprocess,sys
from functools import lru_cache
import numpy as np
import soundfile as sf
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter

ROOT=Path(__file__).resolve().parent;PARENT=ROOT.parent
sys.path.insert(0,str(PARENT))
from render_support import speech_engine,phonemes
W,H,FPS,SR=720,1280,24,24000
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
@lru_cache(maxsize=24)
def font(n):return ImageFont.truetype(FONT,n)

SPEECH=[
 ('GRASS KNOT',"Grass Knot punishes Gyarados's weight. Protean turns Greninja into Grass type. The hit takes thirty-seven percent. Grass damage is neutral here: Water's weakness and Flying's resistance cancel out.", '120 POWER  /  100% ACC  /  1x', '#92EF77'),
 ('DRAGON DANCE',"Gyarados uses Dragon Dance instead of striking back. Attack and Speed rise. It is now faster than Greninja.", 'ATTACK +1  /  SPEED +1', '#FFC47A'),
 ('ICE FANG',"That type change backfires. Ice Fang is now super effective against Grass. It lands for seventy-two percent. Greninja has twenty-eight percent left.", '95% ACC  /  2x VS GRASS', '#A8F3FF'),
 ('ROCK SLIDE',"Rock Slide exploits the Flying weakness, but Greninja's physical Attack is lower. Ninety percent accurate. It lands for twenty-nine percent.", '90% ACC  /  2x VS WATER-FLYING', '#E9C797'),
 ('WATER SHURIKEN',"Water Shuriken moves first despite the speed gap. But Gyarados resists Water. Two hits take only three percent.", 'PRIORITY +1  /  0.5x  /  2 HITS', '#8EDCFF'),
 ('CRUNCH',"Gyarados chooses Crunch: neutral damage, one hundred percent accuracy, and enough power to finish Greninja's remaining health.", '100% ACC  /  1x  /  FINISHER', '#D2AAFF'),
 ('GYARADOS WINS',"Gyarados wins this example with thirty-one percent health. The turning point? Dragon Dance, then Ice Fang.", 'THIS BUILD. THIS BATTLE. THIS RESULT.', '#FFD777'),
]

def voice():
 engine=speech_engine();segments=[];pieces=[];start=0;timeline=[]
 b=json.loads((ROOT/'battle.json').read_text())
 for i,(move,text,note,accent) in enumerate(SPEECH):
  # Punctuation-aware short phrases improve caption timing and preserve attack-name spelling.
  import re
  phrases=[p.strip() for p in re.split(r'(?<=[.!?])\s+',text) if p.strip()]
  segment=[];captions=[];cursor=0
  for phrase in phrases:
   a,sr=engine.create(phonemes(phrase,engine),voice='am_michael',speed=1.18,lang='en-us',is_phonemes=True,sentence_pause=.14,clause_pause=.08)
   if sr!=SR:raise RuntimeError('Unexpected speech sample rate')
   spoken=len(a)/SR;a=np.concatenate([a,np.zeros(round(.12*SR),np.float32)])
   captions.append(dict(text=phrase,start=cursor,duration=spoken+.12));cursor+=len(a)/SR;segment.append(a)
  a=np.concatenate(segment+[np.zeros(round(.24*SR),np.float32)])
  frames=math.ceil(len(a)/SR*FPS);a=np.pad(a,(0,round(frames/FPS*SR)-len(a)))
  duration=len(a)/SR
  e=b['events'][i] if i<6 else None
  timeline.append(dict(index=i,title=move,text=text,note=note,accent=accent,start=start,duration=duration,captions=captions,event=e))
  pieces.append(a);start+=duration
 a=np.concatenate(pieces);fx=np.zeros_like(a);rng=np.random.default_rng(20261024)
 for s in timeline[:6]:
  pos=int((s['start']+.3)*SR);n=int(.40*SR);t=np.arange(n)/SR
  sound=(rng.standard_normal(n)*.035+np.sin(2*np.pi*(110*t+250*t*t))*.06)*np.exp(-t*14)
  fx[pos:pos+n]+=sound[:len(fx[pos:pos+n])]
 sf.write(ROOT/'narration.wav',np.clip(a+fx,-.92,.92),SR)
 story=dict(title='Gyarados vs Greninja: one type change decides the fight',duration=start,segments=timeline,mode='Scripted tactical choices; engine-resolved damage',generation=9)
 (ROOT/'story.json').write_text(json.dumps(story,indent=2));print('NARRATION',round(start,2),flush=True)

def draw_wrap(d,text,x,y,maxw,size=34,fill='white',center=False):
 f=font(size);lines=[];line=''
 for word in text.split():
  trial=(line+' '+word).strip()
  if d.textbbox((0,0),trial,font=f)[2]>maxw and line:lines.append(line);line=word
  else:line=trial
 if line:lines.append(line)
 for line in lines:
  width=d.textbbox((0,0),line,font=f)[2]
  d.text((x+(maxw-width)/2 if center else x,y),line,font=f,fill=fill,stroke_width=1,stroke_fill='#080D19')
  y+=size+10
 return y

def hp_bar(d,label,hp,maxhp,x,y,color,types):
 pct=max(0,min(100,100*hp/maxhp));d.text((x,y),label,font=font(22),fill='white')
 pcttext=f'{round(pct)}%';d.text((x+220,y),pcttext,font=font(22),fill='white')
 d.rounded_rectangle((x,y+34,x+290,y+49),radius=6,fill='#354052')
 if pct>0:d.rounded_rectangle((x,y+34,x+round(290*pct/100),y+49),radius=6,fill=color)
 d.text((x,y+58),types.upper(),font=font(15),fill='#D3DAE6')

def frame(story,scene,art,t,b,loser_art=None):
 i=scene['index'];p=t/scene['duration'];accent=scene['accent']
 # Entire portrait artwork is visible; shallow zoom and alternating pans add motion.
 scaled=ImageOps.fit(art,(W,1080),Image.Resampling.LANCZOS)
 zoom=1.012+.025*p
 scaled=scaled.resize((round(W*zoom),round(1080*zoom)),Image.Resampling.LANCZOS)
 im=Image.new('RGB',(W,H),'#080D19');x=(W-scaled.width)//2+round(3*math.sin(math.pi*p));y=132-(scaled.height-1080)//2
 if i in [2,3,5] and .25<t<.43:x+=round(5*math.sin(t*85))
 im.paste(scaled,(x,y))
 overlay=Image.new('RGBA',(W,H));od=ImageDraw.Draw(overlay)
 od.rectangle((0,0,W,145),fill=(6,11,21,237))
 for yy in range(936,H):od.line((0,yy,W,yy),fill=(6,11,21,round(min(238,(yy-936)*1.6))))
 im=Image.alpha_composite(im.convert('RGBA'),overlay);d=ImageDraw.Draw(im)
 if i==6 and loser_art is not None:
  lw,lh=loser_art.size
  card=ImageOps.fit(loser_art.crop((0,round(lh*.35),round(lw*.49),round(lh*.90))),(230,345),Image.Resampling.LANCZOS)
  im.paste(card,(35,490));d=ImageDraw.Draw(im)
  d.rounded_rectangle((30,484,270,842),radius=10,outline='#D8E2F1',width=3)
  d.rounded_rectangle((30,847,331,887),radius=8,fill='#111C2F')
  d.text((44,858),'GRENINJA: 0 HP',font=font(22),fill='white')
 d.text((30,15),'GYARADOS vs GRENINJA',font=font(22),fill='#F3F7FF')
 before=b['initial'] if i==0 else (b['events'][i]['before'] if i<6 else b['turns'][-1]['after'])
 after=b['events'][i]['after'] if i<6 else before
 mix=max(0,min(1,(t-.20)/.80))
 stats=[]
 for a,z in zip(before,after):stats.append({**z,'hp':a['hp']+(z['hp']-a['hp'])*mix})
 hp_bar(d,'GYARADOS',stats[0]['hp'],394,30,51,'#6BD6FA','Water / Flying')
 gren_types='Grass' if 0<i<6 or (i==0 and mix>.5) else 'Water / Dark'
 hp_bar(d,'GRENINJA',stats[1]['hp'],286,392,51,'#8EEC79',gren_types)
 label=f'ROUND {i//2+1} / 3' if i<6 else 'RESULT'
 d.rounded_rectangle((30,165,226,205),radius=10,fill='#080D19',outline=accent,width=2)
 d.text((44,174),label,font=font(20),fill='white')
 if i==1:
  d.rounded_rectangle((30,225,360,277),radius=10,fill='#10182A')
  d.text((45,240),'SPEED 261 -> 391',font=font(22),fill=accent)
 elif i==2:
  d.rounded_rectangle((30,225,327,277),radius=10,fill='#10182A')
  d.text((45,240),'GRASS IS WEAK TO ICE',font=font(19),fill=accent)
 if i==6:
  d.rounded_rectangle((30,226,388,283),radius=10,fill='#211B0C',outline=accent,width=2)
  d.text((47,240),'WINNER: GYARADOS',font=font(27),fill=accent)
  d.rounded_rectangle((30,302,374,351),radius=10,fill='#10182A')
  d.text((47,314),'GRENINJA: FAINTED',font=font(23),fill='#EEF2FC')
 d.text((30,945),scene['title'],font=font(34),fill=accent,stroke_width=2,stroke_fill='#080D19')
 draw_wrap(d,scene['note'],30,995,660,21,accent)
 # Use sentence audio durations, then distribute short caption chunks inside each phrase.
 chosen=scene['captions'][-1]
 for cap in scene['captions']:
  if cap['start']<=t<cap['start']+cap['duration']:chosen=cap;break
 words=chosen['text'].split();chunks=[' '.join(words[k:k+6]) for k in range(0,len(words),6)]
 q=max(0,min(.999,(t-chosen['start'])/chosen['duration']));line=chunks[min(len(chunks)-1,int(q*len(chunks)))]
 draw_wrap(d,line,36,1050,648,36,center=True)
 absolute=scene['start']+t
 d.rectangle((30,1200,690,1204),fill='#334057');d.rectangle((30,1200,30+660*absolute/story['duration'],1204),fill=accent)
 d.text((30,1227),'LV100  /  GEN9  /  NO ITEMS',font=font(17),fill='#D7DFEC')
 d.text((30,1253),'SCRIPTED CHOICES  /  SIMULATED DAMAGE',font=font(14),fill='#AAB7CC')
 return im.convert('RGB')

def render():
 story=json.loads((ROOT/'story.json').read_text());b=json.loads((ROOT/'battle.json').read_text());paths=json.loads((ROOT/'images.json').read_text())
 args=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(ROOT/'narration.wav'),'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-af','loudnorm=I=-16:TP=-1.5:LRA=9','-movflags','+faststart','-shortest',str(ROOT/'gyarados-greninja-tactical.mp4')]
 proc=subprocess.Popen(args,stdin=subprocess.PIPE)
 loser_art=Image.open(ROOT/paths[7]).convert('RGB') if len(paths)>7 else None
 for s,path in zip(story['segments'],paths[:7]):
  art=Image.open(ROOT/path).convert('RGB')
  for n in range(round(s['duration']*FPS)):
   t=n/FPS;im=frame(story,s,art,t,b,loser_art);proc.stdin.write(im.tobytes())
   if n==round(FPS*.9):im.save(ROOT/f"review-{s['index']+1}.jpg",quality=90)
 proc.stdin.close();rc=proc.wait()
 if rc:raise RuntimeError(f'FFmpeg render failed: {rc}')
 print('RENDERED',flush=True)

if __name__=='__main__':
 if '--render' in sys.argv:render()
 else:voice()
