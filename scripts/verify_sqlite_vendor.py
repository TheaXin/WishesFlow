"""Verify vendored executable SQLite assets before tests or public builds."""
import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'product-site/app/vendor/sql.js'
metadata=json.loads((root/'PROVENANCE.json').read_text())
assert metadata['package']=='sql.js' and metadata['version']=='1.13.0'
for name,expected in metadata['files'].items():
    assert Path(name).name==name
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,name
print('SQLite JS/WASM/license hashes verified')
