"""Actual GPU day/night phases; no campaign writes or invented astronomy."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from tests.browser_planet_orbit import HOOK, open_campaign


def main():
    out = Path('data/orbit-lighting'); out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width':1600, 'height':1000})
        page.add_init_script(HOOK); errors=[]
        page.on('pageerror', lambda e: errors.append(str(e)))
        base='http://127.0.0.1:4211'
        page.goto(base)
        page.wait_for_selector('#campaign-select option[value="scale-demo"]', state='attached')
        if page.locator('[data-dialog-close]').is_visible(): page.locator('[data-dialog-close]').click()
        before=page.request.get(base+'/api/player/campaigns/scale-demo').json()
        open_campaign(page, 'scale-demo')
        page.evaluate("HWTheme.set('dark')")
        page.wait_for_timeout(1000)
        assert 'illustrative' in page.locator('.map-footer').inner_text().lower()
        page.screenshot(path=str(out/'current-dark.png'))
        original_pose=page.evaluate('__orbitAudit.view')
        page.mouse.move(800,600);page.mouse.down();page.mouse.move(1100,600,steps=10);page.mouse.up()
        page.wait_for_timeout(1000)
        assert original_pose!=page.evaluate('__orbitAudit.view')
        page.screenshot(path=str(out/'rotated-dark.png'))
        page.evaluate("HWTheme.set('light')");page.wait_for_timeout(300)
        page.screenshot(path=str(out/'rotated-light.png'))
        result=page.evaluate('''()=>{
          const r=__orbitEngine, gl=r.gl, s=document.createElement('canvas');s.width=64;s.height=32;
          const c=s.getContext('2d');c.fillStyle='white';c.fillRect(0,0,64,32);
          const width=256,height=256,rect={left:0,top:0,width,height};
          let revision=0;
          function sample(longitude,light){
            r.render(s,'lighting-white-'+revision++,width,height,{latitude:0,longitude,distance:2.45},rect,light);
            gl.finish();const pixel=new Uint8Array(4);gl.readPixels(128,128,1,1,gl.RGBA,gl.UNSIGNED_BYTE,pixel);
            const pixels=new Uint8Array(width*height*4);gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
            return {center:Array.from(pixel),alpha:Array.from(pixels.filter((_,i)=>i%4===3))};
          }
          const day=sample(0,[0,0,1]),night=sample(Math.PI,[0,0,1]),half=sample(Math.PI/2,[0,0,1]);
          const fallbackA=sample(0,null),fallbackB=sample(Math.PI,null);
          const neutralGrazing=sample(Math.PI/3,[0,0,1]);
          const relief=document.createElement('canvas');relief.width=64;relief.height=32;
          const rc=relief.getContext('2d');rc.fillStyle='rgb(0,128,128)';rc.fillRect(0,0,64,32);s.hwOrbitRelief=relief;
          const reliefGrazing=sample(Math.PI/3,[0,0,1]);
          rc.fillStyle='rgb(255,128,128)';rc.fillRect(0,0,64,32);
          const oppositeReliefGrazing=sample(Math.PI/3,[0,0,1]);
          return {day:day.center,night:night.center,half:half.center,fallbackA:fallbackA.center,fallbackB:fallbackB.center,
            neutralGrazing:neutralGrazing.center,reliefGrazing:reliefGrazing.center,
            oppositeReliefGrazing:oppositeReliefGrazing.center,
            sameCoverage:day.alpha.every((v,i)=>v===night.alpha[i]&&v===half.alpha[i]),glError:gl.getError()};
        }''')
        assert result['day'][0]>235 and result['night'][0]<20, result
        assert abs(result['fallbackA'][0]-result['fallbackB'][0])>80, result
        assert result['reliefGrazing'][0]>=result['neutralGrazing'][0]*.75, result
        assert result['oppositeReliefGrazing'][0]>=result['neutralGrazing'][0]*.75, result
        assert result['sameCoverage'] and result['glError']==0, result
        assert before==page.request.get(base+'/api/player/campaigns/scale-demo').json()
        assert not errors, errors
        result.update(browser=browser.version, page_errors=errors, records_unchanged=True, actual_drag=True, both_themes=True,
                      limits='Chromium software GPU; white-texture phase measurements, actual demo screenshot. No hardware/Safari claim.')
        (out/'report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
        browser.close()


if __name__=='__main__': main()
