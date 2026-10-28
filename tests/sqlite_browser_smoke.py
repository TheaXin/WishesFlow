"""Actual IndexedDB and Web Locks acceptance; no business data or personal browser profile."""
import functools
import os
import threading
import unittest
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
class BrowserSQLitePersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}/tests/sqlite-harness.html';cls.pw=sync_playwright().start();options={'headless':True}
        if os.environ.get('WISHFLOW_TEST_BROWSER'):options['channel']=os.environ['WISHFLOW_TEST_BROWSER']
        cls.browser=cls.pw.chromium.launch(**options)
    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.server.server_close()
    def test_real_indexeddb_binary_reload_migration_and_cross_tab_lock(self):
        context=self.browser.new_context();page=context.new_page();page.goto(self.url);page.evaluate('window.ready')
        # The old JSON is seeded only in an isolated browser context before migration.
        page.evaluate('''async()=>{await dbStore.close();await new Promise((ok,no)=>{let r=indexedDB.deleteDatabase('wishflow-sqlite-v3');r.onsuccess=ok;r.onerror=no;});localStorage.setItem('wishflow.browser.v1',JSON.stringify({version:1,sources:[{id:'h',title:'原有习惯',kind:'habit',cents:80}],entries:[{sourceId:'h',title:'原有习惯',kind:'habit',cents:80,day:'2026-09-22'}],wishes:[]}));}''')
        page.reload();snapshot=page.evaluate('window.ready');self.assertEqual(snapshot['profiles'][0]['data']['entries'][0]['cents'],80)
        self.assertEqual(page.evaluate('async()=>Array.from((await files.load()).bytes.slice(0,16))'),list(b'SQLite format 3\0'))
        profile=page.evaluate("async()=>await dbStore.select('甲')")
        other=context.new_page();other.goto(self.url);other.evaluate('window.ready')
        # Hold the real origin-wide lock in one tab while another requests a write.
        page.evaluate('''()=>{window.releaseLock=null;window.lockDone=navigator.locks.request('wishflow-sqlite-v3',()=>new Promise(resolve=>{window.releaseLock=resolve;}));}''');page.wait_for_function('window.releaseLock!==null')
        other.evaluate('''id=>{window.writeDone=false;window.pendingWrite=dbStore.addSource(id,'并发来源','attendance','100').then(()=>{window.writeDone=true;});}''',profile)
        self.assertFalse(other.evaluate('window.writeDone'));page.evaluate('()=>window.releaseLock()');other.evaluate('window.pendingWrite')
        page.evaluate('''async id=>{await dbStore.addSource(id,'第二来源','habit','0.70');}''',profile)
        page.reload();snapshot=page.evaluate('window.ready');person=next(p for p in snapshot['profiles'] if p['name']=='甲');self.assertEqual(len(person['data']['sources']),2)
        self.assertIsNotNone(page.evaluate("localStorage.getItem('wishflow.browser.v1')"))
        context.close()
if __name__=='__main__':unittest.main(verbosity=2)
