// The simulator determines outcomes. The calculator only chooses attacks.
const fs = require('node:fs');
const crypto = require('node:crypto');
const {Battle, Dex, TeamValidator} = require('pokemon-showdown');
const calc = require('@smogon/calc');
const BUILDS = JSON.parse(fs.readFileSync(__dirname + '/builds.json', 'utf8'));
const FORMAT = 'gen9nationaldex';
const POLICY = 'Greedy expected direct damage, with priority used for likely knockouts; no switching, Mega, Z-moves, Dynamax or Terastallization. Not perfect play.';

function build(name) {
  const row = BUILDS.find(b => b.species.toLowerCase() === name.toLowerCase());
  if (!row) throw new Error('No validated build for ' + name);
  const set = {...row, level:100, gender:'M', ivs:{hp:31,atk:31,def:31,spa:31,spd:31,spe:31}};
  const errors = new TeamValidator(FORMAT).validateTeam([JSON.parse(JSON.stringify(set))]);
  if (errors) throw new Error(errors.join('; '));
  return set;
}
function seedFor(key) {
  const b = crypto.createHash('sha256').update(key).digest();
  return [0,2,4,6].map(i => b.readUInt16LE(i));
}
function cleanLog(lines) {
  const result=[];
  for(let i=0;i<lines.length;i++) {
    if(lines[i].startsWith('|split|')) { result.push(lines[i+1]); i+=2; }
    else result.push(lines[i]);
  }
  return result;
}
function choice(battle, side) {
  const own = battle.sides[side].active[0], foe = battle.sides[1-side].active[0];
  const request = battle.sides[side].activeRequest;
  const moves = request?.active?.[0]?.moves || [];
  const toCalc = p => new calc.Pokemon(9,p.species.name,{
    level:100, nature:p.set.nature, evs:p.set.evs, ivs:p.set.ivs,
    item:battle.dex.items.get(p.item).name, ability:battle.dex.abilities.get(p.ability).name,
    boosts:p.boosts, status:p.status || undefined, curHP:p.hp,
  });
  const weather = {sunnyday:'Sun',raindance:'Rain',sandstorm:'Sand',hail:'Hail',snow:'Snow'}[battle.field.weather];
  let best = null;
  for(let i=0;i<moves.length;i++) {
    const slot = moves[i]; if(slot.disabled || !slot.pp) continue;
    const move = battle.dex.moves.get(slot.id);
    let damage = 0;
    const result = calc.calculate(9,toCalc(own),toCalc(foe),new calc.Move(9,move.name),new calc.Field({weather}));
    const range = result.range();
    damage = (range[0]+range[1])/2;
    const accuracy = move.accuracy === true ? 1 : move.accuracy/100;
    let score = Math.min(damage,foe.hp)*accuracy;
    if(move.priority > 0 && range[0] >= foe.hp) score += foe.maxhp*2;
    if(!best || score > best.score) best = {index:i+1,score};
  }
  return best ? 'move '+best.index : 'default';
}
function run(a,b,seed) {
  const battle = new Battle({formatid:FORMAT, seed, send:()=>{}});
  const attacks=[];
  const addMove=battle.addMove;
  battle.addMove=function(...args) {
    if(args[0]==='move' && this.activeMove) {
      attacks.push({actor:args[1].side.n,move:args[2],type:this.activeMove.type,
        category:this.activeMove.category,turn:this.turn});
    }
    return addMove.apply(this,args);
  };
  battle.setPlayer('p1',{name:a.species,team:[a]});
  battle.setPlayer('p2',{name:b.species,team:[b]});
  if(battle.requestState === 'teampreview') battle.makeChoices('team 1','team 1');
  let steps=0;
  while(!battle.ended && steps++<80) {
    battle.makeChoices(choice(battle,0),choice(battle,1));
    const errors=battle.log.filter(x=>x.startsWith('|error|'));
    if(errors.length) throw new Error(errors.join('\n'));
  }
  const result={winner:battle.ended ? battle.winner : null,turns:battle.turn,
    log:cleanLog(battle.log),seed,attacks};
  battle.destroy();
  return result;
}
function exampleQuality(result, first, second) {
  const attempts=[0,0], successful=[0,0];
  let current=null;
  for(const line of result.log) {
    const parts=line.split('|');
    if(parts[1]==='move') {
      const actor=parts[2].startsWith('p1')?0:1;
      attempts[actor]++;
      current={actor,counted:false};
    } else if(parts[1]==='-damage' && current && !current.counted &&
              !parts.slice(4).some(p=>p.includes('[from]'))) {
      const target=parts[2].startsWith('p1')?0:1;
      if(target!==current.actor) { successful[current.actor]++;current.counted=true; }
    }
  }
  const side=result.winner===first?0:(result.winner===second?1:null);
  return {attempts,successful,winner_side:side,
    eligible:side!==null && successful[side]>=2 && attempts[1-side]>=1};
}
function matchup(first,second,key,trials=100) {
  if(first===second) throw new Error('Distinct species required');
  if(!Number.isInteger(trials)||trials<1||trials>500) throw new Error('Trial limit');
  const a=build(first),b=build(second), wins={[first]:0,[second]:0,draws:0};
  let representative=null;
  const results=[];
  for(let i=0;i<trials;i++) {
    const result=run(a,b,seedFor(key+':'+i)); results.push(result);
    if(result.winner) wins[result.winner]++; else wins.draws++;
  }
  const favorite=wins[first]===wins[second]?null:(wins[first]>wins[second]?first:second);
  const eligible=results.filter(r=>exampleQuality(r,first,second).eligible);
  const favored=eligible.filter(r=>r.winner===favorite);
  const candidates=favored.length?favored:(eligible.length?eligible:results.filter(r=>r.winner===favorite));
  const pool=(candidates.length?candidates:results).sort((x,y)=>x.turns-y.turns);
  representative=pool[Math.floor(pool.length/2)];
  const presentation={...exampleQuality(representative,first,second),
    eligible_examples:eligible.length,both_sides_won:wins[first]>0&&wins[second]>0,
    selection:'Prefer a multi-attack winning example of the overall favorite; otherwise a qualifying example of the other winner. Aggregate trial outcomes are unchanged.'};
  return {schema:1,key,format:FORMAT,generation:9,level:100,policy:POLICY,
    assumptions:'Fixed legal offensive builds; 31 IVs; 510 or fewer EVs; one item and ability; neutral starting field; abilities may change weather. These builds are not a proof of each species\u2019 absolute peak.',
    builds:[a,b],types:[Dex.species.get(first).types,Dex.species.get(second).types],
    trials,wins,favorite,representative,presentation,simulator_version:require('pokemon-showdown/package.json').version};
}
module.exports={build,matchup,run,cleanLog,BUILDS,choice,exampleQuality};
if(require.main===module) {
  const [a='Charizard',b='Blastoise',key='pilot-v1',n='100']=process.argv.slice(2);
  process.stdout.write(JSON.stringify(matchup(a,b,key,Number(n)),null,2)+'\n');
}
