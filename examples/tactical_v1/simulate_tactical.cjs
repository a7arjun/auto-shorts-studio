const fs=require('fs');
const {Battle,Dex,TeamValidator}=require('pokemon-showdown');
const format='gen9nationaldex';
const builds=[
 {name:'Gyarados',species:'Gyarados',level:100,ability:'Moxie',item:'',nature:'Adamant',evs:{hp:252,atk:4,def:0,spa:0,spd:0,spe:252},ivs:{hp:31,atk:31,def:31,spa:31,spd:31,spe:31},moves:['Dragon Dance','Ice Fang','Crunch','Waterfall']},
 {name:'Greninja',species:'Greninja',level:100,ability:'Protean',item:'',nature:'Timid',evs:{hp:4,atk:0,def:252,spa:0,spd:0,spe:252},ivs:{hp:31,atk:31,def:31,spa:31,spd:31,spe:31},moves:['Grass Knot','Rock Slide','Water Shuriken','Dark Pulse']}
];
const validator=new TeamValidator(format);
for(const set of builds){const errors=validator.validateTeam([structuredClone(set)]);if(errors?.length)throw new Error(errors.join('\n'));}
const moveBanks=builds.map((b,i)=>({pokemon:b.species,equipped:b.moves,reserve:i===0?'Earthquake':'Ice Beam',moves:[...b.moves,i===0?'Earthquake':'Ice Beam'].map(n=>{let m=Dex.moves.get(n);return {name:m.name,type:m.type,category:m.category,base_power:m.basePower,accuracy:m.accuracy,priority:m.priority};})}));
const seed=[2026,10,24,1];
const battle=new Battle({formatid:format,seed,send:()=>{}});
const events=[];let current=null;
const snap=p=>({name:p.name,hp:p.hp,max_hp:p.maxhp,types:p.getTypes(),boosts:{...p.boosts},speed:p.getStat('spe')});
const addMove=battle.addMove;
battle.addMove=function(...args){
 if(args[0]==='move'){
  current={turn:this.turn,actor:args[1].name,move:args[2],before:this.sides.map(s=>snap(s.active[0])),damage:[]};events.push(current);
 }
 return addMove.apply(this,args);
};
const add=battle.add;
battle.add=function(...args){
 if(args[0]==='-damage'&&current&&args[1]?.side){const p=args[1];current.damage.push({target:p.name,hp_after:p.hp,max_hp:p.maxhp});}
 if(args[0]==='-miss'&&current)current.missed=true;
 if(args[0]==='cant'&&current)current.cant=String(args[2]);
 return add.apply(this,args);
};
battle.setPlayer('p1',{name:'Gyarados',team:[builds[0]]});battle.setPlayer('p2',{name:'Greninja',team:[builds[1]]});
if(battle.requestState==='teampreview')battle.makeChoices('team 1','team 1');
const initial=battle.sides.map(s=>snap(s.active[0]));
// Deliberately scripted teaching choices, not a claim of optimal competitive play.
const plans=[['Dragon Dance','Grass Knot'],['Ice Fang','Rock Slide'],['Crunch','Water Shuriken'],['Crunch','Dark Pulse']];
const turns=[];
for(let i=0;i<plans.length&&!battle.ended;i++){
 const choices=plans[i].map((m,s)=>{let idx=battle.sides[s].active[0].moveSlots.findIndex(x=>x.id===Dex.moves.get(m).id);if(idx<0)throw Error('Move not equipped');return 'move '+(idx+1);});
 battle.makeChoices(...choices);turns.push({turn:i+1,planned:plans[i],after:battle.sides.map(s=>snap(s.active[0]))});
 const errors=battle.log.filter(x=>x.startsWith('|error|'));if(errors.length)throw Error(errors.join('\n'));
}
for(let i=0;i<events.length;i++){
 const e=events[i];e.after=i+1<events.length?events[i+1].before:turns[turns.length-1].after;
 const seen=new Set();e.damage=e.damage.filter(d=>{const key=d.target+':'+d.hp_after;if(seen.has(key))return false;seen.add(key);return true;});
 const hp=Object.fromEntries(e.before.map(p=>[p.name,p.hp]));
 for(const d of e.damage){d.hp_lost=hp[d.target]-d.hp_after;hp[d.target]=d.hp_after;d.percent_max_hp=+(100*d.hp_lost/d.max_hp).toFixed(2);}
 e.damage_total=e.damage.reduce((sum,d)=>sum+d.hp_lost,0);
}
const out={schema:1,format,generation:9,seed,policy:'Scripted tactical demonstration; all accuracy, damage rolls, priority, abilities and effects resolved by the pinned Showdown engine. No random-seed search. No items, switching, Mega or Tera. Not optimal-play proof or aggregate win probability.',builds,moveBanks,initial,events,turns,winner:battle.winner||null,ended:battle.ended,log:battle.log,simulator_version:require('pokemon-showdown/package.json').version};
fs.writeFileSync('battle.json',JSON.stringify(out,null,2));console.log(JSON.stringify({initial,events,turns,winner:out.winner,ended:out.ended},null,2));battle.destroy();
