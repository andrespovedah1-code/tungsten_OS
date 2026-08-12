from pathlib import Path
import base64, gzip, hashlib, json, math, re, subprocess

ROOT = Path('.')
fixture_paths = [ROOT / f'demo-fixture-{i}.js' for i in range(1, 5)]

def extract_chunk(path):
    text = path.read_text(encoding='utf-8')
    m = re.search(r"\+'([^']*)';\s*$", text)
    if not m:
        raise SystemExit(f'Could not parse fixture chunk: {path}')
    return m.group(1)

b64 = ''.join(extract_chunk(p) for p in fixture_paths)
payload = json.loads(gzip.decompress(base64.b64decode(b64)).decode('utf-8'))
if payload.get('format') != 'tungsten-backup' or payload.get('version') != 5 or not isinstance(payload.get('state'), dict):
    raise SystemExit('Unexpected Tungsten demo backup contract')

state = payload['state']
if len(state.get('logs', {})) != 21:
    raise SystemExit(f"Expected 21 demo logs, found {len(state.get('logs', {}))}")

# Guided demo contract: loading the populated example should behave like a fresh guided tour.
os_meta = state.setdefault('osMeta', {})
os_meta['tipsOff'] = False
os_meta['tips'] = {}
payload['exportedAt'] = '2026-08-12T17:30:00.000Z'

pillar_ids = {p.get('id') for p in state.setdefault('pillars', [])}
goal_ids = {g.get('id') for g in state.setdefault('goals', [])}
move_ids = {m.get('id') for m in state.setdefault('moves', [])}
calendar = state.setdefault('calendar', {}).setdefault('items', [])
cal_ids = {c.get('id') for c in calendar}

new_pillars = [
    {
        'id':'portafolio','name':'Actualizar portafolio profesional','ico':'briefcase',
        'subtitle':'Convertir trabajo reciente en algo claro que pueda compartir sin explicar demasiado',
        'status':'building','progress':40,'metric':'2 de 5 secciones listas',
        'next':'Escribir el caso corto del tablero de activación',
        'notes':'La estructura ya existe. Falta bajar dos proyectos a casos cortos y pedir una revisión externa.',
        'category':'craft','skillKey':'foco','goalId':'g_portafolio','lastTouched':'2026-08-09','createdAt':'2026-08-01','order':6,
        'sessions':[
            {'id':'ss_p1','date':'2026-08-04','note':'Elegí trabajos que sí muestran criterio y eliminé ejemplos viejos.','mins':55},
            {'id':'ss_p2','date':'2026-08-09','note':'Armé la estructura del caso de activación y seleccioné capturas.','mins':70}
        ]
    },
    {
        'id':'almuerzos','name':'Almuerzos de semana','ico':'home',
        'subtitle':'Resolver parte de la comida de oficina sin depender de comprar algo a última hora',
        'status':'active','progress':50,'metric':'2 de 4 semanas cumplidas',
        'next':'Dejar dos almuerzos listos el domingo',
        'notes':'No busca cocinar perfecto: dos preparaciones simples y una opción de respaldo son suficientes.',
        'category':'self','skillKey':'cocinar','goalId':'g_almuerzos','lastTouched':'2026-08-10','createdAt':'2026-07-28','order':7,
        'sessions':[
            {'id':'ss_m1','date':'2026-08-02','note':'Probé una base de arroz, verduras y pollo que aguantó bien dos días.','mins':65},
            {'id':'ss_m2','date':'2026-08-10','note':'Ajusté cantidades y dejé una lista corta de compras recurrentes.','mins':50}
        ]
    }
]
for item in new_pillars:
    if item['id'] not in pillar_ids:
        state['pillars'].append(item)
        pillar_ids.add(item['id'])

new_goals = [
    {
        'id':'g_portafolio','title':'Dejar el portafolio listo para compartir',
        'why':'Tener una versión breve y actual que muestre cómo pienso y qué he construido, sin armarla de afán cuando aparezca una oportunidad.',
        'kind':'outcome','category':'craft',
        'metrics':[{'id':'gm1','label':'Secciones listas','current':2,'target':5,'unit':'secciones'}],
        'pillarIds':['portafolio'],'createdAt':'2026-08-01'
    },
    {
        'id':'g_almuerzos','title':'Preparar almuerzo en casa 3 días por semana durante 4 semanas',
        'why':'Comer más consistente entre semana y dejar de decidir el almuerzo con hambre y poco tiempo.',
        'kind':'outcome','category':'self',
        'metrics':[{'id':'gm1','label':'Semanas completas','current':2,'target':4,'unit':'semanas'}],
        'pillarIds':['almuerzos'],'createdAt':'2026-07-28'
    }
]
for item in new_goals:
    if item['id'] not in goal_ids:
        state['goals'].append(item)
        goal_ids.add(item['id'])

new_moves = [
    {'id':'mv_17','text':'Escribir el caso corto del tablero para el portafolio','pillarId':'portafolio','goalId':'g_portafolio','skillKey':'foco','prio':1,'done':False,'createdAt':'2026-08-12','dueDate':'2026-08-19'},
    {'id':'mv_18','text':'Pedir una revisión del portafolio a Daniel','pillarId':'portafolio','goalId':'g_portafolio','skillKey':'planear','prio':2,'done':False,'createdAt':'2026-08-12','dueDate':'2026-08-21'},
    {'id':'mv_19','text':'Elegir tres almuerzos que aguanten bien en oficina','pillarId':'almuerzos','goalId':'g_almuerzos','skillKey':'cocinar','prio':2,'done':False,'createdAt':'2026-08-11','dueDate':'2026-08-16'},
    {'id':'mv_20','text':'Dejar dos almuerzos listos el domingo','pillarId':'almuerzos','goalId':'g_almuerzos','skillKey':'cocinar','prio':1,'done':False,'createdAt':'2026-08-12','dueDate':'2026-08-16'}
]
for item in new_moves:
    if item['id'] not in move_ids:
        state['moves'].append(item)
        move_ids.add(item['id'])

new_calendar = [
    {'id':'cal_portafolio','title':'Revisión de portafolio','type':'reminder','date':'2026-08-21','time':'17:30','endTime':'','notes':'Enviar enlace antes y llegar con dos preguntas concretas.','pillarId':'portafolio','goalId':'g_portafolio','repeat':'none','repeatUntil':None,'doneDates':[],'createdAt':'2026-08-12'},
    {'id':'cal_almuerzos','title':'Preparar almuerzos','type':'routine','date':'2026-08-16','time':'18:00','endTime':'19:00','notes':'Dos preparaciones simples para lunes a miércoles.','pillarId':'almuerzos','goalId':'g_almuerzos','repeat':'weekly','repeatUntil':'2026-09-06','doneDates':[],'createdAt':'2026-08-12'}
]
for item in new_calendar:
    if item['id'] not in cal_ids:
        calendar.append(item)
        cal_ids.add(item['id'])

# These are normal measurable Goals, not extra custom Command metrics.
custom_metrics = state.setdefault('metrics', {}).setdefault('custom', [])
if any(m.get('goalId') in {'g_portafolio','g_almuerzos'} for m in custom_metrics):
    raise SystemExit('New demo goals must not create custom Command metrics')

# Referential integrity.
pids = {p['id'] for p in state['pillars']}
gids = {g['id'] for g in state['goals']}
for p in state['pillars']:
    if p.get('goalId') and p['goalId'] not in gids:
        raise SystemExit(f"Dangling project goalId: {p['id']} -> {p['goalId']}")
for g in state['goals']:
    for pid in g.get('pillarIds', []):
        if pid not in pids:
            raise SystemExit(f"Dangling goal pillarId: {g['id']} -> {pid}")
for m in state['moves']:
    if m.get('pillarId') and m['pillarId'] not in pids:
        raise SystemExit(f"Dangling move pillarId: {m['id']} -> {m['pillarId']}")
    if m.get('goalId') and m['goalId'] not in gids:
        raise SystemExit(f"Dangling move goalId: {m['id']} -> {m['goalId']}")
for c in calendar:
    if c.get('pillarId') and c['pillarId'] not in pids:
        raise SystemExit(f"Dangling calendar pillarId: {c['id']} -> {c['pillarId']}")
    if c.get('goalId') and c['goalId'] not in gids:
        raise SystemExit(f"Dangling calendar goalId: {c['id']} -> {c['goalId']}")

if len(state['pillars']) != 8 or len(state['goals']) != 10 or len(state['moves']) != 20 or len(calendar) != 12:
    raise SystemExit(f"Unexpected demo counts: projects={len(state['pillars'])}, goals={len(state['goals'])}, moves={len(state['moves'])}, calendar={len(calendar)}")
if state['osMeta'].get('tipsOff') or state['osMeta'].get('tips') != {}:
    raise SystemExit('Guided demo tip state is not fresh/on')

compact = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
encoded = base64.b64encode(gzip.compress(compact, compresslevel=9, mtime=0)).decode('ascii')
step = math.ceil(len(encoded) / 4)
parts = [encoded[i:i+step] for i in range(0, len(encoded), step)]
while len(parts) < 4:
    parts.append('')
if len(parts) != 4:
    raise SystemExit('Fixture did not split into exactly four chunks')
for i, (path, chunk) in enumerate(zip(fixture_paths, parts), 1):
    path.write_text("window.__TUNGSTEN_DEMO_FIXTURE_GZIP_B64=(window.__TUNGSTEN_DEMO_FIXTURE_GZIP_B64||'')+'" + chunk + "';\n", encoding='utf-8')

# Verify regenerated fixture round-trips byte-for-byte at the JSON-object level.
joined = ''.join(extract_chunk(p) for p in fixture_paths)
roundtrip = json.loads(gzip.decompress(base64.b64decode(joined)).decode('utf-8'))
if roundtrip != payload:
    raise SystemExit('Regenerated fixture round-trip mismatch')

# Make the initial Today advice appear immediately after the demo restore, while
# leaving normal user acknowledgement behavior intact afterward.
demo_path = ROOT / 'demo.html'
demo = demo_path.read_text(encoding='utf-8')
old = "applyAnalysis(analyzed); } catch(e)"
new = "applyAnalysis(analyzed); state.osMeta=state.osMeta||{}; state.osMeta.tipsOff=false; state.osMeta.tips={}; save(); setTimeout(function(){tipHide();tipMaybe(ui.view||'today',true);},700); } catch(e)"
if old in demo:
    if demo.count(old) != 1:
        raise SystemExit(f'Expected one demo load transition, found {demo.count(old)}')
    demo = demo.replace(old, new, 1)
elif new not in demo:
    raise SystemExit('Could not locate demo load transition safely')
demo_path.write_text(demo, encoding='utf-8')

# Syntax-check the only inline executable launcher block (external fixture tags are empty).
blocks = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)</script>', demo, flags=re.I)
if not blocks:
    raise SystemExit('No inline demo launcher script found')
for i, code in enumerate(blocks):
    tmp = Path('/tmp') / f'tungsten-demo-guided-{i}.js'
    tmp.write_text(code, encoding='utf-8')
    subprocess.run(['node', '--check', str(tmp)], check=True)

print('Demo payload SHA-256:', hashlib.sha256(compact).hexdigest())
print('Demo launcher SHA-256:', hashlib.sha256(demo_path.read_bytes()).hexdigest())
print('Counts:', len(state['pillars']), 'projects,', len(state['goals']), 'goals,', len(state['moves']), 'moves,', len(calendar), 'calendar items')
