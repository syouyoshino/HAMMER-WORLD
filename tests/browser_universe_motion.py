"""Actual cosmetic motion, camera response and Universe animation lifecycle."""
import hashlib,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_universe_navigation import HOOK_UNIVERSE


def main():
    out=Path(os.environ.get('WOLD_UNIVERSE_MOTION_OUT','data/universe-space/motion'));out.mkdir(parents=True,exist_ok=True)
    sources=['public/app.js','public/universe-view.js'];hashes=lambda:{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in sources}
    initial=hashes();errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='no-preference',record_video_dir=str(out/'video'),record_video_size={'width':1440,'height':1000})
        context.tracing.start(screenshots=True,snapshots=True);page=context.new_page();page.add_init_script(HOOK_UNIVERSE)
        page.on('pageerror',lambda error:errors.append(str(error)))
        base='http://127.0.0.1:4213';page.goto(base);page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');page.locator('[data-dialog-close]').click()
        before=page.request.get(base+'/api/player/campaigns/nav-demo').json();page.select_option('#campaign-select','nav-demo');page.wait_for_function('document.querySelector("#view-title h1").textContent.includes("Planet")')
        page.select_option('#map-level','universe');page.wait_for_function('window.__universeAudit?.record.level==="universe"');page.evaluate("HWTheme.set('dark')");page.wait_for_timeout(700)
        canvas=page.locator('#planet-map').element_handle();listeners=page.evaluate('__mapListenerAdds')
        pixel=lambda:page.evaluate('document.querySelector("#planet-map").toDataURL()')
        pose=lambda:page.evaluate('__universeAudit.layout.positions.map(p=>({id:p.n.id,x:p.x,y:p.y}))')
        count=lambda:page.evaluate('__universeFrames.length')
        def stopped():
            page.wait_for_timeout(250);n=count();page.wait_for_timeout(450);assert count()==n,(n,count())
        def running():
            n=count();page.wait_for_timeout(600);assert count()>n+2,(n,count())
        running();positions=pose();image_a=pixel();frame_start=count();start=page.evaluate('performance.now()')
        page.screenshot(path=str(out/'01-dark-space.png'));page.wait_for_timeout(1400)
        image_b=pixel();elapsed=page.evaluate('performance.now()')-start;frame_count=count()-frame_start
        assert image_a!=image_b,'Ambient scene must visibly change pixels';assert pose()==positions,'Cosmetic movement must not drift recorded contact targets'
        assert frame_count/elapsed*1000<=28,'Animation must remain bounded'
        page.screenshot(path=str(out/'02-drift.png'))
        region=next(p for p in positions if p['id'].endswith('region-01'))
        page.mouse.move(region['x'],region['y']);page.wait_for_selector('#map-tooltip:visible')
        assert 'open' in page.locator('#map-tooltip').inner_text().lower()
        page.wait_for_timeout(350);assert page.locator('#map-tooltip').is_visible(),'Ambient frames must not erase a hovered contact tooltip'
        assert page.locator('#planet-map').evaluate('n=>getComputedStyle(n).cursor')=='pointer'
        page.mouse.move(10,5);assert page.locator('#map-tooltip').is_hidden()
        page.mouse.move(520,630);page.mouse.down();page.mouse.move(650,660,steps=6);page.mouse.up();page.wait_for_timeout(300)
        assert pose()!=positions;page.screenshot(path=str(out/'03-panned.png'))
        page.emulate_media(reduced_motion='reduce');stopped();quiet_a=pixel();page.wait_for_timeout(400);assert pixel()==quiet_a,'Reduced motion must hold a static image'
        page.locator('#zoom-reset').click();page.evaluate("HWTheme.set('light')");page.wait_for_timeout(200);page.screenshot(path=str(out/'04-light-space.png'))
        page.emulate_media(reduced_motion='no-preference');running()
        # Pause behind real menu/workspace surfaces, then resume from their actual close actions.
        page.locator('#hw-command').click();stopped();page.locator('#command-menu [data-open="economy"]').click();stopped()
        page.locator('[data-return-map]').click();running()
        for _ in range(3):
            page.locator('#hw-command').click();stopped();page.locator('[data-menu-close]').click();running()
        # Inject the visibility event to exercise its lifecycle without claiming OS tab coverage.
        page.evaluate('Object.defineProperty(document,"hidden",{configurable:true,get:()=>true});document.dispatchEvent(new Event("visibilitychange"))');stopped()
        page.evaluate('delete document.hidden;document.dispatchEvent(new Event("visibilitychange"))');running()
        page.select_option('#map-level','galactic');page.wait_for_function('document.querySelector("#view-title h1").textContent.includes("Galactic")');stopped()
        for _ in range(3):
            page.select_option('#map-level','universe');page.wait_for_function('document.querySelector("#view-title h1").textContent.includes("Universe")');running()
            page.select_option('#map-level','galactic');page.wait_for_function('document.querySelector("#view-title h1").textContent.includes("Galactic")');stopped()
        assert page.evaluate('__mapListenerAdds')==listeners
        page.select_option('#map-level','universe');page.wait_for_function('document.querySelector("#view-title h1").textContent.includes("Universe")');running()
        page.select_option('#campaign-select','campaign');page.wait_for_function('document.querySelector("#map-coordinates").textContent.includes("NOT RECORDED")');stopped()
        assert canvas.evaluate('n=>n===document.querySelector("#planet-map")')
        assert before==page.request.get(base+'/api/player/campaigns/nav-demo').json()
        assert not errors and hashes()==initial,errors
        context.tracing.stop(path=str(out/'motion-trace.zip'))
        durations=page.evaluate('__universeFrames');report={'browser':browser.version,'actual_ambient_pixel_change':True,'contact_targets_stable_during_motion':True,'pan_response':True,'hover_action_persists_during_motion':True,'reduced_motion_static':True,'menu_workspace_pause_resume':True,'injected_visibility_pause_resume':True,'exit_reentry_and_campaign_stop':True,'stable_canvas_handlers':True,'same_canvas':True,'records_unchanged':True,'sample_frames':frame_count,'sample_ms':elapsed,'observed_draws_per_second':frame_count/elapsed*1000,'draw_ms_median':sorted(durations)[len(durations)//2],'draw_ms_max':max(durations),'page_errors':errors,'source_hashes':hashes(),'limits':'Software Chromium, one small fixture. Draw-call cost is not frame presentation latency. Visibility is event injection; reduced-motion navigation separately exercised.'}
        (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));context.close();browser.close()


if __name__=='__main__':main()
