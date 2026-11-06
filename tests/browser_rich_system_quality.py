"""Read-only eight-planet chart identity, labels and supported-action checks."""
import hashlib,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK
from tests.browser_navigation_continuity import HOOK_SYSTEM

def check_labels(layout,require_all=False):
    points=layout['positions'];labels=[p for p in points if p['labelRect']];scene=layout['sceneRect']
    if require_all:assert len(labels)==len(points)==8 and len({p['labelPrimary'] for p in labels})==8
    assert layout['hiddenLabelCount']==len(points)-len(labels)
    for i,point in enumerate(labels):
        box=point['labelRect'];assert point['labelPrimary']==point['n']['name'],point
        assert scene['left']<=box['left']<box['right']<=scene['right'] and scene['top']<=box['top']<box['bottom']<=scene['bottom']
        for other in labels[i+1:]:
            rect=other['labelRect'];assert not (box['left']<rect['right'] and box['right']>rect['left'] and box['top']<rect['bottom'] and box['bottom']>rect['top']),(point,other)
        for body in points:
            dx=body['x']-max(box['left'],min(body['x'],box['right']));dy=body['y']-max(box['top'],min(body['y'],box['bottom']));assert dx*dx+dy*dy>body['radius']**2,(point,body)

def main():
    base=os.environ.get('WOLD_RICH_BASE','http://127.0.0.1:4220');cid='continuity-oct31-rich';out=Path(os.environ.get('WOLD_RICH_OUT','data/deep-critique/rich-candidate'));out.mkdir(parents=True,exist_ok=True)
    files=['public/app.js','public/system-view.js','public/universe-view.js','public/desktop-shell.css','public/style.css'];hashes=lambda:{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files};initial=hashes();errors=[]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage']);page=b.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        for hook in [HOOK,HOOK_SYSTEM]:page.add_init_script(hook)
        page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base);page.wait_for_selector('#campaign-select option[value="'+cid+'"]',state='attached');page.locator('[data-dialog-close]').click();page.evaluate("HWTheme.set('dark')");before=page.request.get(base+'/api/player/campaigns/'+cid).json();nodes=before['state']['nodes'];galaxy=next(n for n in nodes if n['kind']=='galaxy');surveyed=[n['id'] for n in nodes if n['kind']=='planet' and n['knowledge']=='surveyed'];page.select_option('#campaign-select',cid);page.wait_for_function('window.__orbitAudit?.result',timeout=90000)
        page.select_option('#map-level','system');page.wait_for_function('window.__systemAudit?.layout.supported');page.wait_for_function('ids=>ids.every(id=>HWSystemPreviewService.stateFor(id)==="ready")',arg=surveyed,timeout=90000)
        crumb=page.locator('#map-breadcrumbs').inner_text();assert crumb.count(galaxy['name'])==1 and 'The Reach' not in crumb,crumb
        layout=page.evaluate('__systemAudit.layout');located={p['n']['id'] for p in layout['model']['located']};visible={p['n']['id'] for p in layout['positions']};assert len(located)==8 and visible==located
        assert all(p['labelRect'] for p in layout['positions']),'Fit should identify all eight bodies while room for labels remains'
        for theme in ['dark','light']:
            page.evaluate('(t)=>HWTheme.set(t)',theme);page.wait_for_timeout(100);check_labels(page.evaluate('__systemAudit.layout'),True);page.screenshot(path=str(out/('system-'+theme+'.png')))
        page.select_option('#system-body-select',surveyed[0]);page.emulate_media(reduced_motion='no-preference');page.locator('#system-focus').focus()
        page.evaluate('''()=>{window.__focusKeyboardAudit={frames:[],blurred:false};document.querySelector('#system-focus').addEventListener('blur',()=>__focusKeyboardAudit.blurred=true,{once:true});
        const sample=()=>{const progress=__systemAudit.view.focusProgress;__focusKeyboardAudit.frames.push({progress,active:document.activeElement.id});if(progress<1)requestAnimationFrame(sample);};requestAnimationFrame(sample);}''')
        page.keyboard.press('Enter');page.wait_for_function('__focusKeyboardAudit.frames.some(frame=>frame.progress===1)')
        keyboard=page.evaluate('__focusKeyboardAudit');(out/'keyboard-focus.json').write_text(json.dumps(keyboard,indent=2));assert not keyboard['blurred'] and all(frame['active']=='system-focus' for frame in keyboard['frames']),keyboard
        assert any(0<frame['progress']<1 for frame in keyboard['frames']),'Keyboard focus must survive intermediate animation frames'
        for theme in ['dark','light']:
            page.evaluate('(t)=>HWTheme.set(t)',theme);page.wait_for_timeout(100);focused=page.evaluate('__systemAudit.layout');check_labels(focused);assert next(p for p in focused['positions'] if p['n']['id']==surveyed[0])['labelRect'];page.screenshot(path=str(out/('system-focused-'+theme+'.png')))
        page.screenshot(path=str(out/'system-keyboard-focus.png'));page.keyboard.press('Tab');assert page.evaluate('document.activeElement.id')=='system-fit-view'
        page.keyboard.press('Space');page.wait_for_function('id=>__systemAudit.view.selectedBodyId===id&&__systemAudit.view.focusProgress===0',arg=surveyed[0]);assert page.evaluate('document.activeElement.id')=='system-fit-view';page.emulate_media(reduced_motion='reduce')
        unknown=next(n for n in nodes if n['kind']=='planet' and n['knowledge']=='detected');page.select_option('#system-body-select',unknown['id']);assert page.locator('#system-orbit').is_disabled() and page.locator('#system-enter').is_disabled();reason=page.locator('#system-selection').inner_text().lower();assert any(term in reason for term in ['unknown','unrecorded','unavailable','not recorded','no recorded']),reason
        page.select_option('#map-level','galactic');page.wait_for_function('document.querySelector("#view-title h1").textContent.includes("Galactic")');assert galaxy['name'] in page.locator('#view-title h1').inner_text();page.screenshot(path=str(out/'galactic-identity.png'))
        assert before==page.request.get(base+'/api/player/campaigns/'+cid).json();assert not errors and initial==hashes(),errors
        report={'browser':b.version,'recorded_planets':sum(n['kind']=='planet' for n in nodes),'located_bodies':len(located),'visible_named_bodies':sum(bool(p['labelRect']) for p in layout['positions']),'unknown_contacts':len(layout['model']['unlocated']),'actual_galaxy_identity':galaxy['name'],'selection_retained_by_fit':True,'unsupported_surface_actions_explained':True,'records_unchanged':True,'page_errors':errors,'source_hashes':hashes(),'limits':'Existing eight-planet fictional fixture, no new records. Read-only desktop Chromium, not a production-density or physical orbital-scale benchmark.'};(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));b.close()

if __name__=='__main__':main()
