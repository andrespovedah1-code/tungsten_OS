from pathlib import Path
import base64, hashlib, re, shutil, subprocess, tarfile, tempfile

ROOT = Path('.')
STAGE = ROOT / '_deploy' / 'landing-r11'
EXPECTED = 'a8134e15a0775cd0cd884b16b7a593ff044af87b2fe3af7e66e8f5b901c435b8'

chunks = sorted(STAGE.glob('chunk-*.txt'))
if not chunks:
    raise SystemExit('No landing payload chunks found')
encoded = ''.join(p.read_text(encoding='utf-8').strip() for p in chunks)
payload = base64.b64decode(encoded, validate=True)
actual = hashlib.sha256(payload).hexdigest()
if actual != EXPECTED:
    raise SystemExit(f'Landing payload checksum mismatch: {actual}')

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    archive = td / 'landing.tar.gz'
    archive.write_bytes(payload)
    with tarfile.open(archive, 'r:gz') as tf:
        tf.extractall(td / 'unpacked')
    src = td / 'unpacked'
    landing = src / 'index.html'
    if not landing.is_file():
        raise SystemExit('Landing index.html missing from payload')
    text = landing.read_text(encoding='utf-8')
    if text.count('./demo.html') < 3:
        raise SystemExit('Landing must contain all demo CTAs')
    for i in range(1, 7):
        rel = f'./assets/landing/tungsten-img-{i}.webp'
        if rel not in text:
            raise SystemExit(f'Landing does not reference {rel}')
        asset = src / 'assets' / 'landing' / f'tungsten-img-{i}.webp'
        if not asset.is_file() or asset.stat().st_size < 10000:
            raise SystemExit(f'Landing asset invalid: {asset}')

    # Preserve the current canonical Tungsten application byte-for-byte.
    app_before = subprocess.check_output(['git', 'hash-object', 'index.html'], text=True).strip()
    shutil.copy2('index.html', 'app.html')
    app_after = subprocess.check_output(['git', 'hash-object', 'app.html'], text=True).strip()
    if app_before != app_after:
        raise SystemExit('app.html does not match the previous canonical index.html')
    if 'tungsten-core-' not in Path('app.html').read_text(encoding='utf-8'):
        raise SystemExit('app.html does not look like Tungsten application source')

    shutil.copy2(landing, 'index.html')
    dest_assets = ROOT / 'assets' / 'landing'
    if dest_assets.exists():
        shutil.rmtree(dest_assets)
    dest_assets.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src / 'assets' / 'landing', dest_assets)

# Demo must bootstrap the canonical app, never the public landing.
demo = Path('demo.html').read_text(encoding='utf-8')
needle = "fetch('./index.html',{cache:'no-store'})"
if demo.count(needle) != 1:
    raise SystemExit(f'Expected exactly one demo app fetch marker, found {demo.count(needle)}')
demo = demo.replace(needle, "fetch('./app.html',{cache:'no-store'})")
demo = demo.replace("No se pudo cargar index.html ('+response.status+').", "No se pudo cargar app.html ('+response.status+').")
Path('demo.html').write_text(demo, encoding='utf-8')

# Lightweight syntax checks for landing inline JS and demo launcher JS.
def check_inline_js(html_path, out_path):
    html = Path(html_path).read_text(encoding='utf-8')
    scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
    code = '\n'.join(s for s in scripts if s.strip())
    Path(out_path).write_text(code, encoding='utf-8')
    subprocess.run(['node', '--check', str(out_path)], check=True)

check_inline_js('index.html', '/tmp/landing-inline.js')
check_inline_js('demo.html', '/tmp/demo-inline.js')

# Final contract checks.
landing_text = Path('index.html').read_text(encoding='utf-8')
if landing_text.count('./demo.html') < 3:
    raise SystemExit('Final landing lost demo links')
if "fetch('./app.html'" not in Path('demo.html').read_text(encoding='utf-8'):
    raise SystemExit('Demo is not wired to app.html')

# Remove one-off deployment scaffolding before committing.
shutil.rmtree(STAGE)
workflow = ROOT / '.github' / 'workflows' / 'landing-r11-deploy.yml'
if workflow.exists():
    workflow.unlink()

subprocess.run(['git', 'add', '--', 'index.html', 'app.html', 'demo.html', 'assets/landing', '_deploy/landing-r11', '.github/workflows/landing-r11-deploy.yml'], check=True)
subprocess.run(['git', 'diff', '--cached', '--check'], check=True)
subprocess.run(['git', 'config', 'user.name', 'github-actions[bot]'], check=True)
subprocess.run(['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'], check=True)
subprocess.run(['git', 'commit', '-m', 'Deploy Tungsten Pro landing and preserve demo app'], check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:landing-r11-deploy'], check=True)
print('Landing deployment validated and committed.')
