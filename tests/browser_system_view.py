"""Actual saved-astronomy solar orbit/pan/zoom, contact picking and camera return."""
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK
from tests.browser_navigation_continuity import HOOK_SYSTEM


def main():
    out=Path('data/navigation-glass/system');out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1440,'height':1000});errors=[]
        for hook in [HOOK,HOOK_SYSTEM]:page.add_init_script(hook)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:4213');page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached')
        if page.locator('[data-dialog-close]').is_visible():page.locator('[data-dialog-close]').click()
        before=page.request.get('http://127.0.0.1:4213/api/player/campaigns/nav-demo').json()
        page.select_option('#campaign-select','nav-demo');page.wait_for_function('window.__orbitAudit?.result',timeout=90000)
        page.evaluate("HWTheme.set('dark')");canvas=page.locator('#planet-map').element_handle()
        page.select_option('#map-level','system');page.wait_for_function('window.__systemAudit?.layout.supported')
        page.wait_for_timeout(500);page.screenshot(path=str(out/'01-system-fit.png'))
        def pose():return page.evaluate('__systemAudit.view')
        def drag(shift=False):
            point=page.evaluate('''()=>{const s=__systemAudit.layout.sceneRect;return {x:(s.left+s.right)/2,y:(s.top+s.bottom)/2}}''')
            if shift:page.keyboard.down('Shift')
            page.mouse.move(point['x'],point['y']);page.mouse.down();page.mouse.move(point['x']+110,point['y']+35,steps=8);page.mouse.up()
            if shift:page.keyboard.up('Shift')
            page.wait_for_timeout(200)
        initial=pose();drag();orbited=pose();assert initial['yaw']!=orbited['yaw'] and initial['pitch']!=orbited['pitch']
        drag(True);panned=pose();assert panned['yaw']==orbited['yaw'] and panned['pitch']==orbited['pitch']
        assert panned['panX']!=orbited['panX'] or panned['panY']!=orbited['panY']
        page.locator('#zoom-in').click();page.wait_for_timeout(600);assert pose()['distance']<panned['distance']
        page.screenshot(path=str(out/'02-free-camera.png'))
        page.locator('#system-fit-view').click();page.wait_for_timeout(200)
        assert pose()==page.evaluate('HWSystemView.fit()'),pose()
        # Put a clipped physical glyph beside a dock row; the visible dock owns the hit.
        collision=page.evaluate('''()=>{const l=__systemAudit.layout,s=l.positions.find(p=>p.n.kind==='star'),m=l.hitTargets.find(p=>p.n.kind==='moon'&&p.uiOnly),r=m.hitRect;
          return {id:m.n.id,dx:l.sceneRect.left+2-s.x,dy:(r.top+r.bottom)/2-s.y,x:r.right-6,y:(r.top+r.bottom)/2};}''')
        page.keyboard.down('Shift');page.mouse.move(700,600);page.mouse.down()
        page.mouse.move(700+collision['dx'],600+collision['dy'],steps=8);page.mouse.up();page.keyboard.up('Shift')
        page.mouse.click(collision['x'],collision['y'])
        page.wait_for_selector(f'#body-focus-view[data-body-id="{collision["id"]}"]:visible')
        page.locator('#body-focus-back').click();page.wait_for_selector('#body-focus-view',state='hidden')
        page.locator('#system-fit-view').click()
        def pick(kind,unlocated=False):
            target=page.evaluate('''({kind,unlocated})=>{const t=__systemAudit.layout.hitTargets.find(p=>p.n.kind===kind&&Boolean(p.uiOnly)===unlocated);if(!t)return null;const r=t.labelRect||t.hitRect;return {id:t.n.id,x:(r.left+r.right)/2,y:(r.top+r.bottom)/2}}''',{'kind':kind,'unlocated':unlocated})
            assert target,(kind,unlocated)
            assert page.evaluate('p=>document.elementFromPoint(p.x,p.y)?.id==="planet-map"',target),target
            page.mouse.click(target['x'],target['y']);return target
        saved=pose();moon=pick('moon',True)
        page.wait_for_selector(f'#body-focus-view[data-body-id="{moon["id"]}"]:visible')
        assert 'Unknown' in page.locator('#body-focus-view').inner_text()
        page.screenshot(path=str(out/'03-unlocated-moon.png'))
        page.locator('#body-focus-back').click();page.wait_for_selector('#body-focus-view',state='hidden');assert pose()==saved
        star=pick('star');page.wait_for_selector(f'#body-focus-view[data-body-id="{star["id"]}"]:visible')
        page.locator('#body-focus-back').click();page.wait_for_selector('#body-focus-view',state='hidden');assert pose()==saved
        planet=pick('planet');page.wait_for_function("document.querySelector('#view-title h1').textContent.includes('Planet')")
        page.wait_for_function("document.querySelector('#orbit-toggle').textContent==='Surface'",timeout=90000)
        page.screenshot(path=str(out/'04-selected-world.png'))
        page.select_option('#map-level','system');page.wait_for_function("document.querySelector('#view-title h1').textContent.includes('System')")
        assert pose()==saved
        page.emulate_media(reduced_motion='reduce');page.locator('#zoom-out').click();page.wait_for_timeout(300)
        assert pose()['distance']>saved['distance']
        page.locator('#system-fit-view').focus();page.keyboard.press('Enter');assert pose()==page.evaluate('HWSystemView.fit()')
        page.set_viewport_size({'width':1280,'height':720});page.wait_for_timeout(300)
        page.screenshot(path=str(out/'05-smaller-desktop.png'))
        for target in page.evaluate('__systemAudit.layout.hitTargets.filter(p=>p.uiOnly)'):
            r=target['hitRect'];assert r['top']>=0 and r['bottom']<=720 and r['left']>=0 and r['right']<=1280,target
        assert canvas.evaluate('c=>c===document.querySelector("#planet-map")')
        assert before==page.request.get('http://127.0.0.1:4213/api/player/campaigns/nav-demo').json()
        assert not errors,errors
        report={'browser':browser.version,'orbit_drag':True,'shift_pan':True,'zoom':True,'fit_keyboard':True,
                'unknown_moon_focus_and_return':True,'rail_owns_clipped_body_hit':True,'star_focus_and_return':True,'planet_click_and_camera_return':True,
                'same_canvas':True,'records_unchanged':True,'reduced_motion':True,'page_errors':errors,
                'source_hashes':{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in ['public/app.js','public/system-view.js','public/body-focus.js','public/planet-orbit.js']},
                'limits':'Desktop Chromium software GPU, frozen recorded astronomy. Enlarged symbols; no physical travel/orbit simulation.'}
        (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));browser.close()


if __name__=='__main__':main()
