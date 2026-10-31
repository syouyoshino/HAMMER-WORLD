// UI return tickets must preserve context without retaining authentication.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const sandbox={window:{},document:{addEventListener(){}}};vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('public/body-focus.js','utf8'),sandbox);
const focus=sandbox.window.HWBodyFocus;
const state={campaignId:'demo',snapshot:{id:'snapshot-a'},contextEpoch:7,
 mapLevel:'planet',mapNodeId:'planet-a',panX:14,panY:-21,zoom:3.5,
 orbitActive:true,orbitView:{latitude:.3,longitude:-2,distance:2.45},
 systemView:{yaw:.4,pitch:.7,distance:2.8},
 entryFocusMarker:{epoch:7,campaignId:'demo',snapshotId:'snapshot-a',planetId:'planet-a',latitude:.2,longitude:-1},
 selectedProvince:'province-a',selectedEntity:{id:'settlement-a'},
 selectedFeatureId:'river-a',selectedFeaturePlanetId:'planet-a',
 selectedFeatureReturnProvince:'province-b',selectedComposition:{kind:'ice',cell:42},
 overlay:'population',mapStyle:'survey',showFeatureNames:true,
 featureListOpen:true,featureListQuery:'river',detailAsset:{version:'planet-detail-v2'},
 detailKey:'asset-a',detailStatus:'SAVED FINE SURFACE',mapRecord:{selected_planet:{id:'planet-a'}},
 orbitTexture:{source:'cached'},orbitTextureKey:'texture-a',orbitInitialKey:'initial-a',
 accessToken:'NEVER_CAPTURE_AUTH',gmToken:'NEVER_CAPTURE_GM'};
const ticket=focus.capture(state);
assert(!JSON.stringify(ticket).includes('NEVER_CAPTURE'));
assert.notEqual(ticket.orbitView,state.orbitView);
assert.notEqual(ticket.systemView,state.systemView);
assert.notEqual(ticket.entryFocusMarker,state.entryFocusMarker);
assert.notEqual(ticket.selectedComposition,state.selectedComposition);
assert.equal(focus.matches(ticket,state),true);
for(const patch of [{campaignId:'other'},{snapshot:{id:'snapshot-b'}},{contextEpoch:8}]){
 const stale={...state,...patch};const before=JSON.stringify(stale);
 assert.equal(focus.restore(ticket,stale),false);
 assert.equal(JSON.stringify(stale),before,'A stale ticket may not alter the new context');
}
const changed={...state,panX:500,panY:600,zoom:1,orbitActive:false,
 orbitView:{latitude:0,longitude:0,distance:4.2},systemView:{yaw:0,pitch:0,distance:5},selectedProvince:null,
 entryFocusMarker:null,
 selectedEntity:null,selectedFeatureId:null,selectedComposition:null,
 overlay:'military',mapStyle:'orbital',showFeatureNames:false};
assert.equal(focus.restore(ticket,changed),true);
for(const key of ['panX','panY','zoom','orbitActive','selectedProvince','selectedFeatureId',
 'selectedFeaturePlanetId','selectedFeatureReturnProvince','overlay','mapStyle','showFeatureNames',
 'featureListOpen','featureListQuery','detailKey','detailStatus','orbitTextureKey','orbitInitialKey']){
 assert.equal(changed[key],state[key],key);
}
assert.equal(JSON.stringify(changed.orbitView),JSON.stringify(state.orbitView));
assert.equal(JSON.stringify(changed.systemView),JSON.stringify(state.systemView));
assert.equal(JSON.stringify(changed.entryFocusMarker),JSON.stringify(state.entryFocusMarker));
assert.equal(changed.selectedEntity,state.selectedEntity);
assert.equal(changed.detailAsset,state.detailAsset);
assert.equal(changed.orbitTexture,state.orbitTexture);
assert.equal(JSON.stringify(changed.selectedComposition),JSON.stringify(state.selectedComposition));
assert.equal(changed.accessToken,state.accessToken);
console.log('Body focus ticket isolation, camera/selection/overlay return and stale-context guards passed');
