const test=require('node:test');
const assert=require('node:assert/strict');
const {BUILDS,build,buildOptions,matchup,cleanLog}=require('./simulate.cjs');

test('every published build is legal in the selected generation and format',()=>{
  for(const row of BUILDS) {
    for(const option of buildOptions(row.species)) assert.equal(option.set.species,row.species);
    const set=build(row.species);
    assert.equal(set.level,100);
    assert.equal(set.moves.length,4);
    assert.ok(Object.values(set.evs).reduce((a,b)=>a+b,0)<=510);
  }
});
test('multi-build game counts use a declared balanced catalogue and the shown build is real',()=>{
  const battle=matchup('Charizard','Garchomp','2026-10-23T22:00+05:30-r3',100);
  assert.deepEqual(battle.build_sampling.counts,[3,3]);
  assert.equal(battle.build_sampling.combination_count,9);
  const totals=battle.build_sampling.strata.map(s=>s.trials);
  assert.equal(totals.reduce((a,b)=>a+b,0),100);
  assert.ok(Math.max(...totals)-Math.min(...totals)<=1);
  assert.deepEqual(battle.builds,battle.representative.builds);
  assert.equal(Object.values(battle.wins).reduce((a,b)=>a+b,0),100);
});
test('repeat seed gives same outcomes and damage events',()=>{
  const a=matchup('Charizard','Blastoise','regression',20);
  const b=matchup('Charizard','Blastoise','regression',20);
  assert.deepEqual(a.wins,b.wins);
  assert.deepEqual(a.representative.log.filter(l=>!l.startsWith('|t:|')),
                   b.representative.log.filter(l=>!l.startsWith('|t:|')));
  assert.equal(a.wins.Charizard+a.wins.Blastoise+a.wins.draws,20);
  assert.ok(a.representative.log.some(l=>l.startsWith('|win|')));
});
test('exact HP events retained once, excluding public rounded duplicate',()=>{
  assert.deepEqual(cleanLog(['|split|p1','|-damage|p1a: A|33/100','|-damage|p1a: A|34/100']),['|-damage|p1a: A|33/100']);
});
test('all catalogue matchups resolve under the documented policy',()=>{
  for(let i=0;i<BUILDS.length;i++) for(let j=i+1;j<BUILDS.length;j++) {
    const b=matchup(BUILDS[i].species,BUILDS[j].species,'smoke',1);
    assert.ok(b.representative.winner,`${BUILDS[i].species} vs ${BUILDS[j].species}`);
  }
});

test('resolved move types include Pixilate, without changing battle outcomes',()=>{
  const battle=matchup('Sylveon','Dragonite','type-test',10);
  const voice=battle.representative.attacks.find(a=>a.move==='Hyper Voice');
  assert.ok(voice);
  assert.equal(voice.type,'Fairy');
  assert.equal(voice.category,'Special');
  assert.equal(Object.values(battle.wins).reduce((a,b)=>a+b,0),10);
});
