const fs=require('fs');const c=require('@smogon/calc');const b=require('./battle.json');
const g=new c.Pokemon(9,'Gyarados',{...b.builds[0],boosts:{atk:1}});
// A null second slot is necessary because this calculator deep-merges species arrays.
const n=new c.Pokemon(9,'Greninja',{...b.builds[1],ability:'No Ability',overrides:{types:['Grass',null]},curHP:80});
const ranges={};for(const move of ['Crunch','Ice Fang','Waterfall'])ranges[move]=c.calculate(9,g,n,new c.Move(9,move)).range();
if(ranges.Crunch[0]<80)throw new Error('Finisher is not a guaranteed damage KO on a successful hit');
b.finish_comparison={defender_types:['Grass'],greninja_remaining_hp:80,ranges};fs.writeFileSync('battle.json',JSON.stringify(b,null,2));console.log(ranges);
