"""Desktop acceptance for separately saved V10 natural geography."""
import hashlib
import copy
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid

import httpx
import psycopg
from psycopg import sql
from playwright.sync_api import sync_playwright
from contextlib import nullcontext
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.store import Store
from app.universe import build_universe


def camera(page):
    return page.evaluate('''async()=>{await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));const t=window.__detailAudit.t;return {ox:t.ox,oy:t.oy,tile:t.tile};}''')


def command(page, view):
    page.click('#hw-command')
    page.locator(f'#command-menu [data-open="{view}"]').click()


def movement_journey(page, db, gm, out):
    """Stage a real fine-map destination, preview/commit it, inspect history."""
    state=db.current('scale-water')['snapshot']['state']
    occupied={u.get('location_id') for u in state['units'] if u['owner']=='player'}
    page.get_by_role('button',name='Forces',exact=True).click()
    page.wait_for_selector('.force-counter.own')
    page.locator('.force-counter.own').first.click()
    page.locator('.force-stack-row').first.get_by_role('button',name='Move',exact=True).click()
    page.get_by_label('Supply source',exact=True).select_option('scale-water-forge')
    page.get_by_role('button',name='Target on map',exact=True).click()
    target=page.evaluate("""occupied=>{const {o,t}=window.__detailAudit,g=o.geometry,d=o.detail,candidates=[];
      for(let y=300;y<800;y+=9)for(let x=200;x<1100;x+=9){
        if(document.elementFromPoint(x,y)?.id!=='planet-map')continue;
        const fx=(x-t.ox)/t.tile,fy=(y-t.oy)/t.tile,point=window.HWMapRenderer.detailAt(g,d,fx,fy);
        if(!point||point.terrain==='o'||'whl'.includes(point.material))continue;
        const cx=((Math.floor(fx)%128)+128)%128,cy=Math.floor(fy),tile=g.tiles[cy*128+cx];
        if(!tile?.province_id||occupied.includes(tile.province_id))continue;
        if([...(t.featureTargets||[]),...(t.provinceTargets||[])].some(r=>x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom))continue;
        candidates.push({x,y,id:tile.province_id,distance:(x-720)**2+(y-540)**2});
      }return candidates.sort((a,b)=>a.distance-b.distance)[0];}""",list(occupied))
    assert target,'No visible canonical land destination for the fixture'
    page.mouse.click(target['x'],target['y'])
    page.wait_for_selector('.force-route.draft',state='attached')
    command(page,'orders')
    packet=db.packet('scale-water')['example'];packet['submission_id']='native-browser-order';packet['orders']['actions']=[]
    if not page.locator('#proposal-json').is_visible():
        page.locator('#proposal-json').locator('xpath=ancestor::details[1]/summary').click()
    page.fill('#proposal-json',json.dumps(packet));page.fill('#gm-token',gm)
    page.get_by_role('button',name='Build proposal from GM packet',exact=True).click()
    built=json.loads(page.locator('#proposal-json').input_value())
    assert built['orders']['actions'][0]['destination_province_id']==target['id']
    assert set(built['orders']['actions'][0])=={'type','unit_id','destination_province_id','source_id'}
    page.click('#preview-order')
    page.wait_for_function("document.querySelector('#order-status').textContent.startsWith('Preview validated')")
    page.locator('[data-return-map]').click();page.screenshot(path=str(out/'07-movement-preview.png'))
    command(page,'orders');page.click('#commit-order')
    page.wait_for_function("document.querySelector('#command-turn').textContent==='TURN 3'")
    page.locator('[data-return-map]').click()
    page.wait_for_function("window.__detailAudit?.o.detail?.version==='planet-detail-v2'")
    live=db.current('scale-water')['snapshot']
    actor=next(u for u in live['state']['units'] if u['id']==built['orders']['actions'][0]['unit_id'])
    assert actor['destination_province_id']==target['id']
    page.screenshot(path=str(out/'08-movement-committed.png'))
    command(page,'history');page.get_by_role('button',name='Inspect turn 0',exact=True).click()
    page.wait_for_function("!document.querySelector('#historical-badge').hidden")
    page.wait_for_function("window.__detailAudit?.o.detail?.version==='planet-detail-v2'")
    command(page,'orders')
    page.wait_for_function("document.querySelector('#orders-panel').textContent.includes('Return to the live campaign revision')")
    assert page.locator('#commit-order').count()==0 or page.locator('#commit-order').is_disabled()
    command(page,'history');page.get_by_role('button',name='Return to live',exact=True).click()
    page.wait_for_function("document.querySelector('#historical-badge').hidden&&document.querySelector('#command-turn').textContent==='TURN 3'")
    assert db.current('scale-water')['snapshot']['state_hash']==live['state_hash']
    page.locator('[data-return-map]').click()
    return {'canonical_destination':target['id'],'native_map_target':True,'preview_commit':True,'historical_read_only':True}


def hold_next_asset(page):
    # Hold a real, fully received Response before the app receives it. This
    # avoids nested synchronous Playwright route handlers racing each other.
    page.evaluate("""()=>{
      const original=window.fetch;window.__nativeOriginalFetch=original;
      window.__releaseNativeAsset=null;window.__staleNativeDecoded=false;let held=false;
      window.fetch=async(...args)=>{
        const response=await original(...args);
        if(held||!String(args[0]).includes('/campaigns/scale-water/detail?'))return response;
        held=true;await response.clone().arrayBuffer();const decode=response.json.bind(response);
        response.json=async()=>{const data=await decode();window.__staleNativeDecoded=true;return data;};
        return await new Promise(resolve=>{window.__releaseNativeAsset=()=>resolve(response);});
      };
    }""")


def release_asset(page):
    page.evaluate('()=>{window.fetch=window.__nativeOriginalFetch;window.__releaseNativeAsset();}')
    page.wait_for_function('window.__staleNativeDecoded===true')
    page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')


def fixture_source():
    """Optional replay of already generated fictional fixtures for UI-only reruns."""
    path=os.environ.get('WOLD_NATIVE_FIXTURE_CACHE')
    if not path:return nullcontext(), 'native-generation'
    cached=json.loads(Path(path).read_text())
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('app').glob('*.py'))}
    assert cached['source_hashes']==hashes,'Fixture cache belongs to different backend source'
    def replay(campaign_id,seed,**kwargs):
        if campaign_id not in cached['states']:return build_universe(campaign_id,seed,**kwargs)
        assert seed==741903 and kwargs['planet_generator']=='planet-v10'
        state=copy.deepcopy(cached['states'][campaign_id])
        assert state['turn']==0 and state['_private']['campaign_id']==campaign_id
        for geo in state['geography'].values():
            for key in ('preset','geology','lake_material','polar_caps'):
                assert geo['surface'][key]==kwargs[key], 'Fixture cache creation options changed'
            digest=geo['detail_ref']['sha256']
            assert cached['assets'][digest]['hydrography']['naming']==kwargs['feature_names']
            kwargs['detail_assets'][digest]=cached['assets'][digest]
        return state
    return patch('app.store.build_universe',replay), 'verified-native-fixture-cache'


def main():
    dsn = os.environ['WOLD_TEST_DATABASE_URL']
    schema = 'browser_detail_' + uuid.uuid4().hex
    out = Path(os.environ.get('WOLD_BROWSER_ARTIFACT_DIR', 'data/planet-scale/browser'))
    out.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    server = None
    try:
        db = Store(dsn, schema=schema)
        fixtures = {'water':('continental','water','water-ice','none'),
                    'lava':('barren','lava','none','cratered'),
                    'hydrocarbon':('frozen','hydrocarbon','water-ice','cratered')}
        source_context,source_kind=fixture_source()
        with source_context:
            for name,(preset,liquid,ice,geology) in fixtures.items():
                db.create_demo_v2('scale-'+name, seed=741903, planet_generator='planet-v10',
                                 preset=preset, lake_material=liquid, polar_caps=ice,
                                 geology=geology, feature_names='generated')
        db.create_demo_v2('scale-old', seed=741903, planet_generator='planet-v9',
                         preset='continental',lake_material='water', feature_names='generated')
        proposal=db.packet('scale-water')['example'];proposal['submission_id']='native-recruit-fixture'
        proposal['orders']['actions']=[{'type':'recruit','settlement_id':'scale-water-forge'}]*2
        db.commit('scale-water',proposal)
        proposal=db.packet('scale-water')['example'];proposal['submission_id']='native-age-fixture';proposal['orders']['actions']=[]
        db.commit('scale-water',proposal)
        db.create_pregame()
        ids=['scale-'+name for name in fixtures]+['scale-old','campaign']
        initial={cid:db.current(cid)['snapshot']['state_hash'] for cid in ids if cid!='campaign'}
        gm,player=secrets.token_urlsafe(32),secrets.token_urlsafe(32)
        env=dict(os.environ,WOLD_DATABASE_URL=dsn,WOLD_DB_SCHEMA=schema,WOLD_ACCESS_MODE='private',
                 WOLD_GM_TOKEN=gm,WOLD_PLAYER_TOKEN=player,WOLD_PLAYER_CAMPAIGNS=','.join(ids))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        base=f'http://127.0.0.1:{port}'
        with tempfile.TemporaryDirectory() as scratch,open(Path(scratch)/'server.log','w') as log:
            server=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1',
                                     '--port',str(port),'--no-access-log'],env=env,stdout=log,stderr=log)
            for _ in range(100):
                try:
                    if httpx.get(base+'/api/access').status_code==200:break
                except httpx.ConnectError:pass
                time.sleep(.1)
            else:raise RuntimeError('Detail QA server did not start')
            with sync_playwright() as pw:
                browser=pw.chromium.launch(executable_path=shutil.which('chromium'),
                                          args=['--no-sandbox','--disable-dev-shm-usage'])
                page=browser.new_page(viewport={'width':1440,'height':1024})
                page.add_init_script('''window.__inputAdds={};const add=EventTarget.prototype.addEventListener;
                EventTarget.prototype.addEventListener=function(type,...rest){
                  if(this===window||this instanceof HTMLCanvasElement&&this.id==='planet-map'){
                    const k=(this===window?'window':'map')+':'+type;window.__inputAdds[k]=(window.__inputAdds[k]||0)+1;
                  }return add.call(this,type,...rest);};''')
                errors=[];responses=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('response',lambda r:responses.append({'url':r.url,'status':r.status}) if '/detail?' in r.url else None)
                page.goto(base)
                page.evaluate('''()=>{const r=window.HWMapRenderer,old=r.drawPlanet;
                  r.drawPlanet=function(ctx,o){const start=performance.now(),t=old(ctx,o);
                    window.__detailAudit={o,t,ms:performance.now()-start};return t;};}''')
                page.fill('#access-token',player);page.click('#login-button')
                page.wait_for_selector('#campaign-select option[value="scale-water"]',state='attached')
                page.locator('[data-dialog-close]').click()
                def select(name, detail=True, surface=True):
                    page.select_option('#campaign-select','scale-'+name)
                    page.wait_for_function('name=>window.__detailAudit?.o.geometry.planet.id.startsWith("scale-"+name+"-")',arg=name)
                    if detail:
                        page.wait_for_function("window.__detailAudit?.o.detail?.version==='planet-detail-v2'",timeout=30000)
                        if surface and page.locator('#orbit-toggle').is_visible() and page.locator('#orbit-toggle').get_attribute('aria-pressed')=='true':
                            page.locator('#orbit-toggle').click()
                            page.wait_for_function("document.querySelector('#orbit-toggle')?.getAttribute('aria-pressed')==='false'")
                    else:page.wait_for_function('!window.__detailAudit?.o.detail')
                select('water',surface=False)
                page.wait_for_function("document.querySelector('#orbit-toggle')?.getAttribute('aria-pressed')==='true'")
                page.screenshot(path=str(out/'00-water-orbit.png'))
                assert page.get_by_role('status').filter(has_text='Drag to orbit').is_visible()
                page.locator('#orbit-toggle').click()
                page.wait_for_function("document.querySelector('#orbit-toggle')?.getAttribute('aria-pressed')==='false'")
                canvas=page.locator('#planet-map').element_handle()
                handlers=page.evaluate('window.__inputAdds')
                c=camera(page)
                if page.locator('#feature-name-toggle').get_attribute('aria-pressed')!='true':page.locator('#feature-name-toggle').click()
                assert camera(page)==c
                home=page.evaluate("window.__detailAudit.t.provinceTargets.find(t=>t.label==='Forge')")
                assert home,'Default native view does not expose the player settlement'
                page.screenshot(path=str(out/'01-water-regional.png'))
                page.mouse.click((home['left']+home['right'])/2,(home['top']+home['bottom'])/2)
                settlement_context=camera(page)
                command(page,'economy');page.wait_for_selector('.local-scope')
                page.locator('.workspace-tabs').get_by_role('button',name='Construction',exact=True).click()
                page.wait_for_selector('.local-construction')
                page.locator('[data-return-map]').click()
                assert camera(page)==settlement_context
                assert page.evaluate('window.__detailAudit.o.selectedProvince')==home['provinceId']
                page.keyboard.press('Escape')
                # Fine natural shores may cross a coarse cell edge. Picking must
                # follow what is drawn while retaining saved province IDs.
                fine_pick = page.evaluate("""()=>{const {o,t}=window.__detailAudit,g=o.geometry,d=o.detail;
                  for(let i=0;i<d.terrain_grid.length;i++){
                    const x=(i%d.width+.5)/8,y=(Math.floor(i/d.width)+.5)/8,parent=Math.floor(y)*128+Math.floor(x),base=g.tiles[parent];
                    if(d.terrain_grid[i]!=='o'||base.terrain==='ocean')continue;
                    const id=d.feature_ids[d.feature_index[i]-1],f=g.detailHydrography.features.find(f=>f.id===id);
                    if(!f||!['ocean','sea'].includes(f.kind))continue;
                    const wx=window.HWMapRenderer.nearestX(x,(720-t.ox)/t.tile,128),sx=t.ox+wx*t.tile,sy=t.oy+y*t.tile;
                    if(sx<220||sx>1050||sy<280||sy>780||document.elementFromPoint(sx,sy)?.id!=='planet-map')continue;
                    if([...(t.featureTargets||[]),...(t.provinceTargets||[])].some(r=>sx>=r.left&&sx<=r.right&&sy>=r.top&&sy<=r.bottom))continue;
                    return {x:sx,y:sy,id,name:f.name};
                  }return null;}""")
                assert fine_pick,'Fixture lacks a visible refined water cell'
                page.mouse.move(fine_pick['x'],fine_pick['y']);page.wait_for_selector('#map-tooltip:not([hidden])')
                assert fine_pick['name'] in page.locator('#map-tooltip').inner_text()
                page.mouse.click(fine_pick['x'],fine_pick['y'])
                page.wait_for_function('id=>document.querySelector("#inspector-content").dataset.selectedHydroFeature===id',arg=fine_pick['id'])
                page.screenshot(path=str(out/'01a-fine-coast-selection.png'))
                page.keyboard.press('Escape')
                page.locator('#zoom-reset').click();page.screenshot(path=str(out/'02-water-overview.png'))
                for _ in range(7):page.locator('#zoom-in').click()
                page.screenshot(path=str(out/'03-water-detail.png'))
                detail_camera=camera(page)
                # Pointer-anchored descent must preserve the geographic point.
                before=camera(page);page.mouse.move(720,540);page.mouse.wheel(0,-100);page.wait_for_timeout(120)
                after=camera(page)
                for axis,at in [('ox',720),('oy',540)]:
                    assert abs((at-before[axis])/before['tile']-(at-after[axis])/after['tile'])<.03
                before=camera(page)
                page.mouse.move(720,540);page.mouse.down();page.mouse.move(1040,590,steps=10);page.mouse.up()
                assert camera(page)!=before
                # Existing feature list resolves saved IDs on the refined map.
                page.locator('#feature-list-button').click()
                search=page.get_by_role('searchbox',name='Find recorded features')
                search.fill('river')
                assert page.locator('.hydro-feature-row:visible').count()>0
                assert all('River' in text for text in page.locator('.hydro-feature-row:visible').all_inner_texts())
                search.fill('no-such-chart-feature-xyz')
                assert page.locator('.hydro-feature-row:visible').count()==0
                assert page.get_by_text('No recorded features match').is_visible()
                search.fill('')
                assert page.locator('.hydro-feature-row:visible').count()==page.evaluate('window.__detailAudit.o.geometry.detailHydrography.features.length')
                page.locator('.hydro-feature-row').first.click()
                page.wait_for_selector('#inspector-content[data-selected-hydro-feature]')
                selected=page.locator('#inspector-content').get_attribute('data-selected-hydro-feature')
                context=camera(page);page.keyboard.press('Escape');assert camera(page)==context
                page.click('#hw-command');page.locator('#command-menu [data-open="economy"]').click()
                page.wait_for_selector('[data-return-map]')
                page.locator('[data-return-map]').click();assert camera(page)==context
                assert page.evaluate('window.__detailAudit.o.selectedFeatureId')==selected
                page.screenshot(path=str(out/'04-detail-return.png'))
                for name in ['lava','hydrocarbon']:
                    select(name);page.locator('#zoom-reset').click()
                    for _ in range(5):page.locator('#zoom-in').click()
                    page.screenshot(path=str(out/f'05-{name}-detail.png'))
                select('old',False);page.screenshot(path=str(out/'06-legacy.png'))
                for _ in range(6):
                    select('water');select('old',False)
                assert canvas.evaluate('c=>c===document.querySelector("#planet-map")')
                assert page.evaluate('window.__inputAdds')==handlers,'Input handlers accumulated'
                # An intentionally delayed asset must not survive a campaign switch.
                hold_next_asset(page)
                page.select_option('#campaign-select','scale-water')
                page.wait_for_function('typeof window.__releaseNativeAsset==="function"')
                page.select_option('#campaign-select','scale-old')
                page.wait_for_function('window.__detailAudit?.o.geometry.planet.id.startsWith("scale-old-")')
                release_asset(page)
                assert page.evaluate('!window.__detailAudit.o.detail')
                assert all(db.current(cid)['snapshot']['state_hash']==h for cid,h in initial.items())
                select('water')
                movement=movement_journey(page,db,gm,out)
                storage=page.evaluate('JSON.stringify({local:{...localStorage},session:{...sessionStorage}})')
                assert player not in storage and gm not in storage
                select('old',False)
                hold_next_asset(page)
                page.select_option('#campaign-select','scale-water')
                page.wait_for_function('typeof window.__releaseNativeAsset==="function"')
                command(page,'campaign');page.click('#logout-button')
                page.wait_for_function("document.querySelector('#campaign-select').options.length===1")
                release_asset(page)
                assert page.locator('#map-placeholder').is_visible()
                assert page.locator('#feature-list-button').is_disabled()
                assert page.locator('.hydro-feature-row').count()==0
                assert page.locator('.orbit-landmark').count()==0
                assert not errors,errors
                report={'browser':browser.version,'viewport':[1440,1024],'fixtures':list(fixtures),
                        'detail_dimensions':[1024,640],'fixture_source':source_kind,'pointer_zoom_preserves_point':True,
                        'initial_v10_orbit_and_surface_action':True,
                        'management_return_preserves_context':True,'canonical_feature_selection':selected,'refined_water_pick':fine_pick,
                        'repeated_switch_handlers_stable':True,'canvas_persistent':True,
                        'source_records_unchanged_before_supported_commit':True,'movement':movement,'page_errors':errors,
                        'detail_responses':responses,'detail_camera':detail_camera,
                        'source_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('public').glob('*.js')}}
                (out/'workflow.json').write_text(json.dumps(report,indent=2)+'\n')
                print(json.dumps(report,indent=2));browser.close()
    finally:
        if server:server.terminate();server.wait(timeout=10)
        with psycopg.connect(dsn,autocommit=True) as c:
            c.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


if __name__=='__main__':main()
