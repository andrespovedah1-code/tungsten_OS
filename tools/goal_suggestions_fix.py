from pathlib import Path
from collections import Counter
import hashlib
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'index.html'
ZIP = ROOT / 'Tungsten_OS_suggested_goals_fix.zip'

src = INDEX.read_text(encoding='utf-8')
before = src


def one(old, new, label):
    global src
    n = src.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {n}')
    src = src.replace(old, new, 1)


css = r'''
/* ROUND DB · Suggested Goals: no check circle, stable hover, selection via accent border. */
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested{transition:border-color .14s var(--ease),background .14s var(--ease)!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested:hover{transform:none!important;box-shadow:none!important;border-color:color-mix(in srgb,var(--gc) 58%,var(--line2))!important;background:radial-gradient(112px 78px at 100% 0%,color-mix(in srgb,var(--gc) 15%,transparent),transparent 72%),linear-gradient(160deg,var(--raise),var(--panel))!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested.on{border-color:var(--gc)!important;box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--gc) 34%,transparent)!important;background:radial-gradient(126px 88px at 100% 0%,color-mix(in srgb,var(--gc) 22%,transparent),transparent 72%),linear-gradient(160deg,color-mix(in srgb,var(--gc) 7%,var(--raise)),var(--panel))!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested .wiz-goal-board-foot{justify-content:flex-start!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested .wiz-goal-route-chip{max-width:100%!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested .wiz-goal-board-metric strong{max-width:72%!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;line-height:1.15!important;text-wrap:balance}
.modal.wiz.is-goals .wiz-goal-board-grid:has(.wiz-goal-board-card.is-suggested:nth-child(11)){grid-auto-rows:minmax(148px,auto)!important}
'''
one('</style>', css + '\n</style>', 'append suggested-goal CSS')

old_card = "      return '<div role=\"button\" tabindex=\"0\" class=\"wiz-goal-board-card' + (on ? ' on' : '') + (linkNames.length ? ' is-linked' : '') + '\" style=\"--gc:' + c + '\" data-act=\"wizGoal\" data-kind=\"outcome\" data-id=\"' + esc(g.id) + '\">' +"
new_card = "      return '<div role=\"button\" tabindex=\"0\" class=\"wiz-goal-board-card' + (on ? ' on' : '') + (linkNames.length ? ' is-linked' : '') + (activeTab === 'linked' ? ' is-suggested' : '') + '\" style=\"--gc:' + c + '\" data-act=\"wizGoal\" data-kind=\"outcome\" data-id=\"' + esc(g.id) + '\">' +"
one(old_card, new_card, 'add suggested-card class')

old_check = "          (linkNames.length ? '<span class=\"wiz-goal-route-chip\">' + ico('briefcase') + '<span>' + esc(linkLabel) + '</span></span>' : '<span class=\"wiz-goal-route-chip quiet\" aria-hidden=\"true\"></span>') +\n          '<span class=\"wiz-goal-board-check\">' + ico('check') + '</span></div></div>';"
new_check = "          (linkNames.length ? '<span class=\"wiz-goal-route-chip\">' + ico('briefcase') + '<span>' + esc(linkLabel) + '</span></span>' : '<span class=\"wiz-goal-route-chip quiet\" aria-hidden=\"true\"></span>') +\n          (activeTab === 'linked' ? '' : '<span class=\"wiz-goal-board-check\">' + ico('check') + '</span>') + '</div></div>';"
one(old_check, new_check, 'remove circular check from suggested cards only')

one("tr('suggested finish lines','destinos sugeridos')", "tr('suggested goals','metas sugeridas')", 'linked-tab wording')
one("tr('Finish lines suggested by your Projects','Destinos sugeridos por tus Proyectos')", "tr('Measurable Goals suggested for your Projects','Metas medibles sugeridas para tus Proyectos')", 'linked-board title')

route = re.search(r"    const projectRoute = selectedProjects\.length\n      \? .*?\n      : .*?;\n", src, flags=re.S)
if not route:
    raise SystemExit('remove Ruta actual: block not found')
src = src[:route.start()] + "    const projectRoute = '';\n" + src[route.end():]

# gp_carrera was already referenced by the Sport project and Fitness quick-start,
# but the canonical measurable Goal preset itself was missing. Restore it as Yo #10.
checkup = "  { id:'gp_checkup', kind:'outcome', cat:'self', name:'Completar un chequeo preventivo', nameEn:'Complete a preventive health check', why:'Resolver pendientes básicos de salud con información real.', whyEn:'Resolve basic health unknowns with real information.', metric:'Chequeo completado', metricEn:'Checkup completed', unit:'%', unitEn:'%', current:0, target:100 },"
race = "  { id:'gp_carrera', kind:'outcome', cat:'self', name:'Completar una carrera de 10K', nameEn:'Complete a 10K race', why:'Convertir el entrenamiento en un resultado concreto y medible.', whyEn:'Turn training into a concrete, measurable result.', metric:'Distancia de carrera', metricEn:'Race distance', unit:'km', unitEn:'km', current:0, target:10 },"
one(checkup, checkup + '\n' + race, 'restore missing tenth Self / Yo goal')

# Goal catalog integrity.
goals_block = src.split('const GOAL_PRESETS = [', 1)[1].split('];', 1)[0]
outcome_lines = [line for line in goals_block.splitlines() if "kind:'outcome'" in line]
counts = Counter(re.search(r"cat:'([^']+)'", line).group(1) for line in outcome_lines)
expected = {'revenue': 10, 'capital': 10, 'craft': 10, 'self': 10, 'life': 10}
if dict(counts) != expected:
    raise SystemExit(f'goal category count regression: {dict(counts)} != {expected}')

mapping_block = src.split('const PROJECT_GOAL_PRESETS = Object.freeze({', 1)[1].split('});', 1)[0]
mapped_ids = set(re.findall(r"'(gp_[^']+)'", mapping_block))
defined_ids = set(re.findall(r"id:'(gp_[^']+)'", goals_block))
dangling = sorted(mapped_ids - defined_ids)
if dangling:
    raise SystemExit('PROJECT_GOAL_PRESETS contains unknown goal ids: ' + ', '.join(dangling))

# Every measurable Goal added in the recent expansion round must remain reachable
# from at least one Project suggestion. gp_carrera is also included because it was
# already part of the intended Project/quick-start relationship contract.
new_round = goals_block.split('/* ROUND CX', 1)[1].split("{ id:'vp_disciplina'", 1)[0]
new_ids = set(re.findall(r"id:'(gp_[^']+)'", new_round)) | {'gp_carrera'}
orphan_new = sorted(new_ids - mapped_ids)
if orphan_new:
    raise SystemExit('new measurable presets without Project suggestions: ' + ', '.join(orphan_new))

# Quick-start references must also resolve to canonical presets.
quick_block = src.split('const QUICK_START_PACKS = {', 1)[1].split('};', 1)[0]
quick_goal_ids = set(re.findall(r"'(gp_[^']+)'", quick_block))
dangling_quick = sorted(quick_goal_ids - defined_ids)
if dangling_quick:
    raise SystemExit('QUICK_START_PACKS contains unknown goal ids: ' + ', '.join(dangling_quick))

if src == before:
    raise SystemExit('patch made no changes')
INDEX.write_text(src, encoding='utf-8')

# JavaScript syntax integrity for every inline script block.
scripts = re.findall(r'<script(?:\s[^>]*)?>([\s\S]*?)</script>', src, flags=re.I)
if not scripts:
    raise SystemExit('no inline scripts found')
for i, code in enumerate(scripts):
    tmp = Path('/tmp') / f'tungsten-inline-{i}.js'
    tmp.write_text(code, encoding='utf-8')
    subprocess.run(['node', '--check', str(tmp)], check=True)

# Package modified source + pristine backup + demo entry files.
pkg = Path('/tmp/tungsten-goal-fix-package')
if pkg.exists():
    shutil.rmtree(pkg)
(pkg / 'backup').mkdir(parents=True)
(pkg / 'index.html').write_text(src, encoding='utf-8')
(pkg / 'backup' / 'index.before.html').write_text(before, encoding='utf-8')
for name in ['demo.html', 'demo-fixture-1.js', 'demo-fixture-2.js', 'demo-fixture-3.js', 'demo-fixture-4.js']:
    f = ROOT / name
    if f.exists():
        shutil.copy2(f, pkg / name)

changelog = '''Suggested Goals onboarding repair
- Project-suggested Goal cards no longer use the circular check affordance.
- Selected Project-suggested Goal cards use their category accent border.
- Project-suggested card hover no longer lifts/jumps.
- Long target values get more room and linked boards use taller scrolling rows.
- Removed Current route / Ruta actual.
- Renamed the linked board to Measurable Goals suggested for your Projects / Metas medibles sugeridas para tus Proyectos.
- Restored the missing tenth Self / Yo measurable Goal: Complete a 10K race / Completar una carrera de 10K.
- Repaired the existing gp_carrera Project + Fitness quick-start relationship by restoring its canonical Goal preset.
- Validated exactly 10 measurable Goal presets in every category.
- Validated every measurable preset from the recent expansion round is connected to at least one Project suggestion.
- Validated Project suggestion and Quick-start Goal references resolve to canonical Goal presets.
'''
(pkg / 'CHANGELOG.txt').write_text(changelog, encoding='utf-8')

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

sums = f"{sha256(pkg / 'index.html')}  index.html\n{sha256(pkg / 'backup' / 'index.before.html')}  backup/index.before.html\n"
(pkg / 'SHA256SUMS.txt').write_text(sums, encoding='utf-8')
if ZIP.exists():
    ZIP.unlink()
with zipfile.ZipFile(ZIP, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for f in sorted(pkg.rglob('*')):
        if f.is_file():
            z.write(f, f.relative_to(pkg))

print('Goal counts:', dict(counts))
print('Validated recent project-linked goal presets:', len(new_ids))
print('Inline JS blocks syntax-checked:', len(scripts))
print('ZIP:', ZIP)
