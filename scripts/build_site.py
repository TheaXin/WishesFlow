"""Build the public site from tracked source, including an exact commit link."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build():
    revision = os.environ.get('GITHUB_SHA') or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    repository = os.environ.get('GITHUB_REPOSITORY', 'TheaXin/WishesFlow')
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=normal'], cwd=ROOT, text=True).strip())
    output = ROOT / 'site-dist'
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(ROOT / 'product-site', output)
    # Browsers may retain the previous release's JS/CSS after HTML updates.
    # Address every local entry resource by this release to keep them coherent.
    for document in output.rglob('*.html'):
        html = document.read_text()
        def versioned(match):
            url = match.group(2)
            if url.startswith(('http:', 'https:', '//', 'data:')):
                return match.group(0)
            return match.group(1) + url + '?v=' + revision + match.group(3)
        document.write_text(re.sub(r'''((?:src|href)=["'])([^"'?]+\.(?:js|css))(["'])''', versioned, html))
    metadata = {'commit': revision, 'source': f'https://github.com/{repository}/commit/{revision}', 'dirty': dirty}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2) + '\n')
    script = 'window.WISHFLOW_BUILD = ' + json.dumps(metadata) + ';\n'
    script += "document.querySelectorAll('#build-source').forEach(a => { a.href=window.WISHFLOW_BUILD.source; a.textContent='源码版本 '+window.WISHFLOW_BUILD.commit.slice(0,7)+(window.WISHFLOW_BUILD.dirty ? '（含本地未提交修改）' : ''); });\n"
    (output / 'version.js').write_text(script)
    print(f'Built {output} from {revision[:7]}; uncommitted changes: {dirty}')

if __name__ == '__main__':
    build()
