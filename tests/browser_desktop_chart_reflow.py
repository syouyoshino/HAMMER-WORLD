"""Desktop hierarchy/control reachability across all maps and CSS zoom."""
import hashlib,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK
from tests.browser_navigation_continuity import HOOK_SYSTEM
from tests.browser_coherent_navigation import ATLAS_HOOK

def main():
    out=Path(os.environ.get('WOLD_REFLOW_OUT','data/deep-critique/reflow'));out.mkdir(parents=True,exist_ok=True)
    files=['public/app.js','public/index.html','public/style.css','public/desktop-shell.css','public/desktop-shell.js','public/universe-view.js'];hashes=lambda:{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files};initial=hashes();errors=[];checks=[]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage']);page=b.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        for hook in [HOOK,HOOK_SYSTEM,ATLAS_HOOK]:page.add_init_script(hook)
        page.on('pageerror',lambda e:errors.append(str(e)));base='http://127.0.0.1:4213';page.goto(base);page.wait_for_selector('#campaign-select option[value="nav-demo"]',state='attached');page.locator('[data-dialog-close]').click();before=page.request.get(base+'/api/player/campaigns/nav-demo').json();page.select_option('#campaign-select','nav-demo');page.wait_for_function('window.__orbitAudit?.result',timeout=90000);map_canvas=page.locator('#planet-map').element_handle()
        for width,height,zoom in [(1440,1000,1),(1280,720,1),(1280,720,1.5)]:
            page.set_viewport_size({'width':width,'height':height});page.evaluate('(z)=>document.documentElement.style.zoom=z',str(zoom));page.wait_for_timeout(250)
            for level in ['universe','galactic','sector','system','planet']:
                control=page.locator('#map-level');control.click(trial=True);control.select_option(level);page.wait_for_function('v=>document.querySelector("#map-level").value===v&&document.querySelector("#view-title h1").textContent.includes(v[0].toUpperCase()+v.slice(1))',arg=level,timeout=90000);page.wait_for_function('!document.querySelector("#zoom-in").disabled&&!document.querySelector("#zoom-out").disabled',timeout=90000);page.wait_for_timeout(250)
                # Native mode/destination controls remain hit-test reachable.
                for selector in ['#map-level','#zoom-in','#zoom-out','#zoom-reset','#map-recenter']:
                    button=page.locator(selector)
                    if button.is_visible() and button.is_enabled():
                        rect=button.bounding_box();assert rect and rect['x']>=-1 and rect['y']>=-1 and rect['x']+rect['width']<=width+1 and rect['y']+rect['height']<=height+1,(level,zoom,selector,rect)
                        button.click(trial=True)
                if level in ['universe','galactic','sector','system']:
                    for selector in ['#map-style','#overlay-select','#feature-name-toggle','#feature-list-button']:assert page.locator(selector).is_hidden(),(level,selector)
                # Focus scrolls long ladders into view, preserving normal keyboard access.
                crumbs=page.locator('#map-breadcrumbs button:not(:disabled)')
                for i in range(crumbs.count()):
                    crumb=crumbs.nth(i)
                    if not crumb.is_visible():continue
                    crumb.focus();crumb.click(trial=True)
                page.mouse.move(20,20);page.screenshot(path=str(out/f'{width}-{height}-{zoom}-{level}.png'));checks.append({'viewport':[width,height],'css_zoom':zoom,'level':level,'controls_reachable':True})
                if level in ['galactic','sector']:
                    layout=page.evaluate('__chartAudit.layout');safe=layout['safeRect'];short=safe['height']<420
                    targets=[p for p in layout['positions'] if p['y']-25>=safe['top'] and p['y']+(88 if short else 124)<=safe['bottom'] and p['hitRect']['left']>=safe['left'] and p['hitRect']['right']<=safe['right']];assert targets,('Need a complete actionable system card',width,height,zoom,level,safe,layout['contactAnchors'])
                    unknown={n['id'] for n in layout['model']['systems'] if n.get('x') is None or n.get('y') is None};shown={p['n']['id'] for p in layout['hitTargets'] if p.get('uiOnly')};assert unknown<=shown,('Unlocated fixture systems must remain visible',unknown,shown)
                    target=targets[0];point=page.evaluate('''p=>{const c=document.querySelector('#planet-map'),r=c.getBoundingClientRect();return{x:r.left+p.x*r.width/c.clientWidth,y:r.top+p.y*r.height/c.clientHeight};}''',{'x':target['x'],'y':target['y']+(80 if short else 115)});assert page.evaluate('p=>document.elementFromPoint(p.x,p.y)?.id',point)=='planet-map';page.mouse.click(point['x'],point['y']);page.wait_for_function('document.querySelector("#map-level").value==="system"');page.wait_for_function('window.__systemAudit?.layout.supported');checks[-1]['open_system_clicked']=True;checks[-1]['complete_card_visible']=True;checks[-1]['unlocated_fixture_visible']=True
                elif level=='system':
                    page.select_option('#system-body-select','nav-demo-planet-reach');page.locator('#system-focus').focus();page.keyboard.press('Enter');page.wait_for_function('__systemAudit.view.focusProgress===1');page.locator('#system-fit-view').focus();page.keyboard.press('Space');page.wait_for_function('__systemAudit.view.focusProgress===0&&__systemAudit.view.selectedBodyId==="nav-demo-planet-reach"');checks[-1]['body_selection_and_fit']=True
        assert map_canvas.evaluate('n=>n===document.querySelector("#planet-map")');assert before==page.request.get(base+'/api/player/campaigns/nav-demo').json();assert not errors and hashes()==initial,errors
        report={'browser':b.version,'checks':checks,'same_canvas':True,'records_unchanged':True,'page_errors':errors,'source_hashes':hashes(),'limits':'Desktop Chromium and CSS zoom, not native browser zoom or mobile/Safari certification. Trial clicks verify hit testing without changing each framing setting.'};(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));b.close()

if __name__=='__main__':main()
