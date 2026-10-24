const fs=require('fs');const {Dex,TeamValidator}=require('pokemon-showdown');
const pools={
Pikachu:['Thunderbolt','Quick Attack','Iron Tail','Electro Ball','Grass Knot'],
Raichu:['Thunderbolt','Volt Switch','Focus Blast','Grass Knot','Nasty Plot'],
Charizard:['Flamethrower','Air Slash','Dragon Pulse','Solar Beam','Roost'],
Blastoise:['Hydro Pump','Ice Beam','Dark Pulse','Aura Sphere','Shell Smash'],
Venusaur:['Giga Drain','Sludge Bomb','Earth Power','Sleep Powder','Synthesis'],
Gyarados:['Dragon Dance','Ice Fang','Crunch','Waterfall','Earthquake'],
Greninja:['Grass Knot','Rock Slide','Water Shuriken','Dark Pulse','Ice Beam'],
Dragonite:['Dragon Claw','Extreme Speed','Earthquake','Fire Punch','Dragon Dance'],
Garchomp:['Earthquake','Dragon Claw','Rock Slide','Poison Jab','Swords Dance'],
Lucario:['Aura Sphere','Close Combat','Flash Cannon','Extreme Speed','Swords Dance'],
Gengar:['Shadow Ball','Sludge Bomb','Focus Blast','Thunderbolt','Destiny Bond'],
Alakazam:['Psychic','Shadow Ball','Focus Blast','Energy Ball','Calm Mind'],
Machamp:['Close Combat','Dynamic Punch','Stone Edge','Ice Punch','Bullet Punch'],
Arcanine:['Flare Blitz','Extreme Speed','Crunch','Wild Charge','Will-O-Wisp'],
Ninetales:['Flamethrower','Energy Ball','Solar Beam','Will-O-Wisp','Nasty Plot'],
Snorlax:['Body Slam','Crunch','Earthquake','Rest','Curse'],
Lapras:['Surf','Ice Beam','Thunderbolt','Freeze-Dry','Sing'],
Jolteon:['Thunderbolt','Shadow Ball','Volt Switch','Hyper Voice','Substitute'],
Vaporeon:['Surf','Ice Beam','Shadow Ball','Wish','Protect'],
Flareon:['Flare Blitz','Superpower','Quick Attack','Will-O-Wisp','Wish'],
Espeon:['Psychic','Dazzling Gleam','Shadow Ball','Morning Sun','Calm Mind'],
Umbreon:['Foul Play','Dark Pulse','Wish','Protect','Toxic'],
Leafeon:['Leaf Blade','X-Scissor','Knock Off','Quick Attack','Swords Dance'],
Glaceon:['Ice Beam','Freeze-Dry','Shadow Ball','Water Pulse','Wish'],
Sylveon:['Moonblast','Hyper Voice','Mystical Fire','Quick Attack','Calm Mind'],
Eevee:['Quick Attack','Bite','Swift','Sand Attack','Tackle'],
Meowth:['Fake Out','Pay Day','Fury Swipes','Bite','Taunt'],
Tyranitar:['Stone Edge','Crunch','Earthquake','Ice Punch','Dragon Dance'],
Scizor:['Bullet Punch','U-turn','Close Combat','Knock Off','Swords Dance'],
Heracross:['Megahorn','Close Combat','Stone Edge','Knock Off','Swords Dance'],
Gardevoir:['Moonblast','Psychic','Shadow Ball','Mystical Fire','Calm Mind'],
Gallade:['Psycho Cut','Close Combat','Leaf Blade','Shadow Sneak','Swords Dance'],
Salamence:['Dragon Claw','Dual Wingbeat','Earthquake','Flamethrower','Dragon Dance'],
Metagross:['Meteor Mash','Zen Headbutt','Earthquake','Bullet Punch','Agility'],
Milotic:['Surf','Ice Beam','Dragon Pulse','Recover','Haze'],
Sceptile:['Leaf Blade','Dragon Pulse','Focus Blast','Acrobatics','Swords Dance'],
Blaziken:['Flare Blitz','Close Combat','Thunder Punch','Stone Edge','Swords Dance'],
Swampert:['Waterfall','Earthquake','Ice Punch','Rock Slide','Stealth Rock'],
Infernape:['Flare Blitz','Close Combat','Mach Punch','Grass Knot','U-turn'],
Empoleon:['Surf','Flash Cannon','Ice Beam','Grass Knot','Roost'],
Torterra:['Wood Hammer','Earthquake','Stone Edge','Crunch','Shell Smash'],
Luxray:['Wild Charge','Crunch','Ice Fang','Play Rough','Thunder Wave'],
Weavile:['Icicle Crash','Knock Off','Ice Shard','Low Kick','Swords Dance'],
Mamoswine:['Earthquake','Icicle Crash','Ice Shard','Stone Edge','Stealth Rock'],
Togekiss:['Air Slash','Dazzling Gleam','Aura Sphere','Roost','Thunder Wave'],
Excadrill:['Earthquake','Iron Head','Rock Slide','Rapid Spin','Swords Dance'],
Chandelure:['Flamethrower','Shadow Ball','Energy Ball','Psychic','Calm Mind'],
Haxorus:['Dragon Claw','Earthquake','Poison Jab','Close Combat','Dragon Dance'],
Hydreigon:['Dark Pulse','Dragon Pulse','Flamethrower','Earth Power','Nasty Plot'],
Goodra:['Dragon Pulse','Sludge Bomb','Flamethrower','Thunderbolt','Hydro Pump']
};
const validator=new TeamValidator('gen9nationaldex');const errors=[];const entries=[];
for(const [name,moves] of Object.entries(pools)){
 const species=Dex.species.get(name);const selected={Greninja:'Protean',Gyarados:'Moxie',Garchomp:'Rough Skin',Glaceon:'Ice Body'};const ability=selected[name]||species.abilities['0'];
 for(let omit=0;omit<5;omit++){
  const set={name,species:name,ability,level:100,item:'',nature:'Serious',evs:{hp:4,atk:0,def:0,spa:0,spd:0,spe:0},moves:moves.filter((_,i)=>i!==omit)};
  const e=validator.validateTeam([set]);if(e?.length)errors.push({name,omit,errors:e});
 }
 entries.push({species:name,types:species.types,weight_kg:species.weightkg,base_stats:species.baseStats,validated_ability:ability,available_abilities:species.abilities,
  moves:moves.map(n=>{const m=Dex.moves.get(n);if(!m.exists)throw Error('Unknown move '+n);return {name:m.name,id:m.id,type:m.type,category:m.category,base_power:m.basePower,accuracy:m.accuracy,priority:m.priority,description:m.shortDesc,selection_note:m.basePower===0&&m.category!=='Status'?'Variable power: resolve in engine before explaining damage.':undefined};}),validation:{all_five_four_move_subsets:true,level:100,no_items:true,nature:'Serious',evs:'4 HP baseline; validate the final production build separately'}});
}
if(errors.length){console.error([...new Set(errors.flatMap(x=>x.errors))].join('\n'));process.exit(1);}
if(entries.length!==50)throw Error('Expected 50 species');
const out={version:1,format:'gen9nationaldex',simulator_version:require('pokemon-showdown/package.json').version,scope:'50 species, five legal move options each, equip only four. All five four-of-five subsets validated with the stated ability and baseline build. Curated options are not usage rankings or proof of optimal play. Revalidate changed ability/build/rules before production.',validated_sets:250,pokemon:entries};
fs.writeFileSync(process.argv[2] || require('path').join(__dirname,'tactical_moves.json'),JSON.stringify(out,null,2));console.log('Validated 50 Pokemon, 250 moves and 250 four-move subsets.');
