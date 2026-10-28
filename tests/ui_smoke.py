"""Real browser acceptance tests. Run after scripts/build_site.py, separately from stdlib tests."""
import functools
import json
import os
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

class BrowserAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(ROOT/'site-dist')))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}/app/'
        cls.pw=sync_playwright().start();options={'headless':True}
        if os.environ.get('WISHFLOW_TEST_BROWSER'): options['channel']=os.environ['WISHFLOW_TEST_BROWSER']
        cls.browser=cls.pw.chromium.launch(**options)
        (ROOT/'test-results').mkdir(exist_ok=True)
    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.server.server_close()
    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
        self.page=self.context.new_page();self.errors=[]
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.page.goto(self.base);expect(self.page.locator('#nickname')).to_be_visible()
    def tearDown(self):
        self.context.close();self.assertEqual(self.errors,[])
    def login(self,name):
        self.page.locator('#nickname').fill(name);self.page.locator('#profile-form button').click();expect(self.page.locator('#home-heading')).to_have_text(name+' 的个人首页')
    def route(self,name):
        # Mobile navigation is collapsible; visit via the real menu.
        menu=self.page.locator('#menu-toggle')
        if menu.is_visible() and menu.get_attribute('aria-expanded')=='false': menu.click()
        self.page.locator('[data-route="'+name+'"]').click()
        if name=='home':
            expect(self.page.locator('#welcome:visible, #page-home:visible')).to_have_count(1)
            return
        expect(self.page.locator('#page-'+name)).to_be_visible()
    def test_five_page_flow_historical_dates_isolation_and_refresh(self):
        p=self.page;self.login('验收甲')
        p.locator('#first-wish-title').fill('演唱会');p.locator('#first-wish-amount').fill('80');p.locator('#home-wish-form button').click()
        expect(p.locator('#home-next')).to_contain_text('配置一个行动')
        self.route('attendance');p.locator('#income-title').fill('稳定工作');p.locator('#income-amount').fill('100');p.locator('#income-form button').click()
        p.locator('#attendance-date').fill('2026-09-23');p.locator('#attendance-date').dispatch_event('change');p.locator('#attendance-submit').click();expect(p.locator('#attendance-submit')).to_be_disabled();expect(p.locator('#attendance-state')).to_contain_text('已经打卡')
        self.route('habits');p.locator('#habit-title').fill('阅读20分钟');p.locator('#habit-amount').fill('20.29');p.locator('#habit-form button').click()
        p.locator('#habit-date').fill('2026-09-22');p.locator('#habit-date').dispatch_event('change');p.get_by_role('button',name='完成习惯：阅读20分钟',exact=True).click();expect(p.get_by_role('button',name='当日已完成：阅读20分钟',exact=True)).to_be_disabled()
        self.route('dashboard');expect(p.locator('#dashboard-metrics')).to_contain_text('¥120.29');expect(p.locator('#trend svg')).to_be_visible()
        p.locator('#trend summary').click();rows=p.locator('#trend tbody tr');expect(rows).to_have_count(2);expect(rows.nth(0)).to_contain_text('2026-09-22');expect(rows.nth(1)).to_contain_text('¥120.29')
        p.screenshot(path=str(ROOT/'test-results'/'dashboard-desktop.png'),full_page=True)
        self.route('wishes');p.get_by_role('button',name='解锁这个心愿',exact=True).click();p.get_by_role('button',name='标记为已实现 ✦',exact=True).click();expect(p.locator('#wish-balance')).to_have_text('¥40.29');expect(p.locator('.wish-card.completed')).to_contain_text('演唱会')
        p.screenshot(path=str(ROOT/'test-results'/'wishes-desktop.png'),full_page=True)
        p.reload();expect(p.locator('#wish-balance')).to_have_text('¥40.29')
        p.locator('#switch-profile').click();self.login('验收乙');expect(p.locator('#home-wish-form')).to_be_visible();self.route('dashboard');expect(p.locator('#dashboard-metrics')).to_contain_text('¥0.00');expect(p.locator('#history')).not_to_contain_text('稳定工作')
        p.locator('#switch-profile').click();p.get_by_role('button',name='验收甲',exact=True).click();self.route('wishes');expect(p.locator('#wish-balance')).to_have_text('¥40.29')
    def test_migration_export_restore_cancel_and_invalid_file(self):
        p=self.page;old={'version':1,'sources':[{'id':'h','title':'旧阅读','kind':'habit','cents':1000}],'entries':[{'sourceId':'h','title':'旧阅读','kind':'habit','cents':1000,'day':'2026-09-23'}],'wishes':[]}
        raw=json.dumps(old,ensure_ascii=False)
        p.evaluate('(raw)=>localStorage.setItem("wishflow.browser.v1",raw)',raw);p.reload();p.get_by_role('button',name='旧版资料',exact=True).click();self.route('dashboard');expect(p.locator('#dashboard-metrics')).to_contain_text('¥10.00');self.assertEqual(p.evaluate('localStorage.getItem("wishflow.browser.v1")'),raw)
        self.route('data')
        with p.expect_download() as download: p.locator('#export').click()
        contents=Path(download.value.path()).read_text();backup=json.loads(contents);self.assertEqual(backup['profiles'][0]['data'],old)
        before=p.evaluate('localStorage.getItem("wishflow.browser.v2")')
        p.locator('#import').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'{"version":99}'})
        expect(p.locator('#notice')).to_contain_text('导入失败');self.assertEqual(p.evaluate('localStorage.getItem("wishflow.browser.v2")'),before)
        p.once('dialog',lambda d:d.dismiss());p.locator('#import').set_input_files({'name':'backup.json','mimeType':'application/json','buffer':contents.encode()});p.wait_for_function('document.getElementById("import").value===""');self.assertEqual(p.evaluate('localStorage.getItem("wishflow.browser.v2")'),before)
        p.once('dialog',lambda d:d.accept());p.locator('#import').set_input_files({'name':'backup.json','mimeType':'application/json','buffer':contents.encode()});expect(p.locator('#notice')).to_contain_text('备份已恢复');self.route('home');p.get_by_role('button',name='旧版资料',exact=True).click();self.route('dashboard');expect(p.locator('#dashboard-metrics')).to_contain_text('¥10.00')
    def test_storage_failure_blocks_save_and_corruption_preserves_raw(self):
        p=self.page;self.login('验收')
        p.evaluate('() => {Storage.prototype.setItem=function(){throw new DOMException("full","QuotaExceededError")}}')
        p.locator('#first-wish-title').fill('不应保存');p.locator('#home-wish-form button').click();expect(p.locator('#notice')).to_contain_text('此次操作未保存');self.assertEqual(p.evaluate('JSON.parse(localStorage.getItem("wishflow.browser.v2")).profiles[0].data.wishes.length'),0)
        p.reload();p.evaluate('localStorage.setItem("wishflow.browser.v2","broken")');p.reload();expect(p.locator('#notice')).to_contain_text('现有记录未被覆盖');self.assertEqual(p.evaluate('localStorage.getItem("wishflow.browser.v2")'),'broken')
    def test_tabs_keep_independent_selections_and_refresh_shared_database(self):
        p=self.page;self.login('标签甲');p.locator('#first-wish-title').fill('甲的心愿');p.locator('#home-wish-form button').click()
        other=self.context.new_page();other.goto(self.base);expect(other.locator('#nickname')).to_be_visible();other.locator('#nickname').fill('标签乙');other.locator('#profile-form button').click();expect(other.locator('#home-heading')).to_have_text('标签乙 的个人首页')
        other.locator('#first-wish-title').fill('乙的心愿');other.locator('#home-wish-form button').click()
        self.route('wishes');expect(p.locator('#wish-list')).to_contain_text('甲的心愿');expect(p.locator('#wish-list')).not_to_contain_text('乙的心愿')
        other.locator('[data-route=wishes]').click();expect(other.locator('#wish-list')).to_contain_text('乙的心愿');expect(other.locator('#wish-list')).not_to_contain_text('甲的心愿')
        p.reload();other.reload();expect(p.locator('#profile-name')).to_have_text('标签甲');expect(other.locator('#profile-name')).to_have_text('标签乙');self.assertEqual(p.evaluate('JSON.parse(localStorage.getItem("wishflow.browser.v2")).profiles.length'),2)

    def test_mobile_navigation_and_each_page_has_no_horizontal_overflow(self):
        p=self.page;self.login('手机验收')
        # Layouts with real data, not just empty screens.
        d={'version':1,'sources':[{'id':'w','title':'稳定工作','kind':'attendance','cents':100000},{'id':'h','title':'阅读20分钟','kind':'habit','cents':2000}],'entries':[{'sourceId':'w','title':'稳定工作','kind':'attendance','cents':100000,'day':'2026-09-22'},{'sourceId':'h','title':'阅读20分钟','kind':'habit','cents':2000,'day':'2026-09-23'}],'wishes':[{'id':'a','title':'看一场演唱会','cents':150000,'priority':1,'status':'active'},{'id':'c','title':'读一本喜欢的书','cents':10000,'priority':2,'status':'completed'}]}
        p.evaluate('(data)=>{const db=JSON.parse(localStorage.getItem("wishflow.browser.v2"));db.profiles[0].data=data;localStorage.setItem("wishflow.browser.v2",JSON.stringify(db))}',d)
        p.reload();p.set_viewport_size({'width':390,'height':844})
        for route in ['home','dashboard','attendance','habits','wishes','data']:
            self.route(route);expect(p.locator('#app-nav')).to_be_hidden();self.assertEqual(p.evaluate('document.documentElement.scrollWidth'),390,route)
            p.screenshot(path=str(ROOT/'test-results'/('qa-'+route+'.png')),full_page=True)
        self.route('wishes');p.locator('[data-filter=completed]').click();expect(p.locator('.wish-card')).to_have_count(1);expect(p.locator('.wish-card')).to_contain_text('读一本喜欢的书')
        self.route('attendance');p.locator('#attendance-date').fill('2099-01-01');p.locator('#attendance-date').dispatch_event('change');expect(p.locator('#attendance-submit')).to_be_disabled()

if __name__=='__main__':unittest.main(verbosity=2)
