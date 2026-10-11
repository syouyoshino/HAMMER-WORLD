"""Optional browser smoke test. Requires Playwright and WOLD_TEST_DATABASE_URL.
Run: python tests/browser_smoke.py [chromium|webkit]. Uses a disposable PG schema.
"""
import os,sys,tempfile,secrets,subprocess,socket,time,json,uuid,shutil
import psycopg
from psycopg import sql
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.store import Store
scratch=tempfile.TemporaryDirectory()
dsn=os.environ['WOLD_TEST_DATABASE_URL']; schema='browser_'+uuid.uuid4().hex
with psycopg.connect(dsn,autocommit=True) as c:c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
db=Store(dsn,schema=schema); db.create_demo(); db.create_pregame()
token=secrets.token_urlsafe(32); env=os.environ.copy(); env.update(WOLD_DATABASE_URL=dsn,WOLD_DB_SCHEMA=schema,WOLD_GM_TOKEN=token,WOLD_ACCESS_MODE='local')
with socket.socket() as s: s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
base=f'http://127.0.0.1:{port}'; log=open(Path(scratch.name)/'server.log','w+')
server=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(port),'--no-access-log'],env=env,stdout=log,stderr=log)
try:
    for _ in range(60):
        try:
            if httpx.get(base+'/api/player/campaigns').status_code==200: break
        except httpx.ConnectError: pass
        time.sleep(.1)
    else: raise RuntimeError('server readiness failed')
    with sync_playwright() as p:
        kind=sys.argv[1] if len(sys.argv)>1 else 'chromium'
        if kind=='webkit':browser=p.webkit.launch(headless=True)
        else:
            executable=os.environ.get('WOLD_CHROMIUM_EXECUTABLE') or shutil.which('chromium')
            browser=p.chromium.launch(executable_path=executable,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1); page.set_default_timeout(10000)
        errors=[]; page.on('pageerror',lambda error: errors.append(str(error)))
        page.goto(base); page.wait_for_selector('#campaign-select option',state='attached')
        page.wait_for_function("document.querySelector('#turn-badge').textContent === 'TURN 0'")
        assert page.locator('#campaign-select').input_value()=='demo'
        page.wait_for_function('document.fonts.status === \"loaded\"')
        assert page.locator('.desktop').evaluate('(el)=>getComputedStyle(el).backgroundColor')=='rgb(192, 192, 192)'
        assert page.locator('.titlebar').evaluate('(el)=>getComputedStyle(el).backgroundColor')=='rgb(0, 0, 128)'
        bar=page.locator('[data-drag-pane=turn-window]'); bar.scroll_into_view_if_needed()
        box=bar.bounding_box(); original=page.locator('#turn-window').bounding_box()
        page.mouse.move(box['x']+60,box['y']+10); page.mouse.down(); page.mouse.move(box['x']+80,box['y']+20,steps=4); page.mouse.up()
        moved=page.locator('#turn-window').bounding_box(); assert abs(moved['x']-original['x']-20)<2
        page.click('#reset-layout'); assert page.locator('#turn-window').evaluate('(el)=>getComputedStyle(el).transform')=='none'
        page.locator('#map-panel').scroll_into_view_if_needed(); box=page.locator('#map-panel').bounding_box(); old_canvas=page.locator('#planet-map').bounding_box()['height']
        if kind=='webkit':
            assert page.locator('#map-panel').evaluate('(el)=>getComputedStyle(el).resize')=='both'
            page.locator('#map-panel').evaluate('(el)=>el.style.height="380px"')
            page.wait_for_timeout(100)
        else:
            page.mouse.move(box['x']+box['width']-3,box['y']+box['height']-3); page.mouse.down(); page.mouse.move(box['x']+box['width']-43,box['y']+box['height']-63,steps=6); page.mouse.up()
            resized=page.locator('#map-panel').bounding_box(); assert resized['height']<box['height']-20,(resized,box)
            assert page.locator('#planet-map').bounding_box()['height']<old_canvas-20
        page.click('#reset-layout'); page.locator('.center-column').evaluate('(el)=>el.scrollTop=0')
        page.screenshot(path='/tmp/hammer-world-desktop.png',full_page=True)
        page.click('#zoom-in'); assert page.locator('#zoom-reset').inner_text()=='120%'
        page.click('#zoom-reset'); page.select_option('#overlay-select','provinces'); page.select_option('#overlay-select','terrain')
        data=httpx.get(base+'/api/player/campaigns/demo').json()['state']; land=next(t for t in data['tiles'] if t['province_id'])
        box=page.locator('#planet-map').bounding_box(); tile=min(box['width']/64,box['height']/40)
        x=box['x']+(box['width']-64*tile)/2+(land['x']+.5)*tile; y=box['y']+(box['height']-40*tile)/2+(land['y']+.5)*tile
        page.mouse.move(x,y); page.mouse.click(x,y); assert 'Province population' in page.locator('#inspector-content').inner_text()
        page.click('.nav-item[data-view="orders"]'); page.fill('#gm-token',token)
        page.get_by_role('button',name='Load example proposal').click(); page.wait_for_function("document.querySelector('#proposal-json').value.length > 50")
        proposal=json.loads(page.locator('#proposal-json').input_value()); proposal['orders']={'farmers':400,'miners':200,'technicians':100}; proposal['narrative']='Verified demonstration production turn.'
        page.fill('#proposal-json',json.dumps(proposal)); assert page.locator('#commit-order').is_disabled()
        page.click('#preview-order'); page.wait_for_function("!document.querySelector('#commit-order').disabled")
        assert httpx.get(base+'/api/player/campaigns/demo').json()['turn']==0
        page.click('#commit-order'); page.wait_for_function("document.querySelector('#turn-badge').textContent === 'TURN 1'")
        after=httpx.get(base+'/api/player/campaigns/demo').json(); assert after['state']['ore']==2800 and after['state']['food']==8000
        report=page.locator('#turn-report .report-line').all_text_contents()
        assert report==['Food produced1,200','Food consumed1,200','Ore produced400','Energy produced200','Population lost0'], report
        page.click('.nav-item[data-view="history"]'); page.get_by_label('Inspect turn 0',exact=True).click()
        page.wait_for_function("document.querySelector('#historical-badge').hidden === false"); assert page.locator('#turn-badge').inner_text()=='TURN 0'
        page.click('.nav-item[data-view="orders"]'); assert 'Return to the live' in page.locator('#orders-panel').inner_text()
        page.click('.nav-item[data-view="history"]'); page.get_by_role('button',name='Return to live').click(); page.wait_for_function("document.querySelector('#turn-badge').textContent === 'TURN 1'")
        def dialogs(dialog):
            dialog.accept('qa-branch') if dialog.type=='prompt' else dialog.accept()
        page.on('dialog',dialogs); page.get_by_label('Restore turn 0 into a new branch',exact=True).click()
        page.wait_for_function("document.querySelector('#campaign-select').value === 'qa-branch'"); page.wait_for_function("document.querySelector('#turn-badge').textContent === 'TURN 0'")
        assert httpx.get(base+'/api/player/campaigns/demo').json()['turn']==1
        page.select_option('#campaign-select','campaign'); page.wait_for_function("document.querySelector('#turn-badge').textContent === 'TURN —'")
        assert 'UNKNOWN' in page.locator('#resource-strip').inner_text(); assert page.locator('#map-placeholder').is_visible()
        page.select_option('#campaign-select','demo'); page.wait_for_function("document.querySelector('#turn-badge').textContent === 'TURN 1'")
        page.click('.nav-item[data-view="planet"]'); page.locator('.center-column').evaluate('(el)=>el.scrollTop=0'); page.evaluate('document.querySelector(".toast")?.remove()'); page.screenshot(path='/tmp/hammer-world-desktop-turn1.png',full_page=True)
        page.set_viewport_size({'width':390,'height':844}); page.screenshot(path='/tmp/hammer-world-mobile.png',full_page=True)
        overflow=page.evaluate('document.documentElement.scrollWidth > window.innerWidth'); assert not overflow; assert page.locator('.resource-card').evaluate_all('(els)=>els.every(el=>el.scrollWidth<=el.clientWidth)'); assert not errors,errors
        print(json.dumps({'browser':kind,'browser_workflow':'PASS','flows':['classic colors/pixel font','window drag/native resize/reset','planet zoom/overlay/selection','preview no writes','commit','historic read-only','restore branch','pregame unknown'],'page_errors':errors,'mobile_horizontal_overflow':overflow}))
        browser.close()
finally:
    server.terminate(); server.wait(timeout=10); log.close(); scratch.cleanup()
    with psycopg.connect(dsn,autocommit=True) as c:c.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
