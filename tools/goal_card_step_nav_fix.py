from pathlib import Path
import hashlib
import re
import subprocess

p = Path('index.html')
s = p.read_text(encoding='utf-8')
expected_before = '53267ab31ecec1f7c16f5744cbee3324303fd00647a4350db7d33abcddf41c21'
before = hashlib.sha256(s.encode()).hexdigest()
if before != expected_before:
    raise SystemExit(f'Unexpected base index hash: {before} != {expected_before}')


def one(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 match, found {n}')
    s = s.replace(old, new, 1)


one(
    ".wiz-steps i{flex:1;height:3px;border-radius:99px;background:var(--line2);transition:background .3s var(--ease)}\n.wiz-steps i.done{background:var(--hot)}",
    ".wiz-steps .wiz-step-bar{flex:1;height:3px;min-width:0;border-radius:99px;background:var(--line2);transition:background .3s var(--ease);cursor:pointer}\n.wiz-steps .wiz-step-bar.done{background:var(--hot)}",
    'wizard step CSS',
)

old_steps = "  $('obSteps').innerHTML = [1,2,3,4,5,6].map(function (i) { return '<i class=\"' + (typeof st === 'number' && i <= st ? 'done' : '') + '\"></i>'; }).join('');"
new_steps = "  $('obSteps').innerHTML = [1,2,3,4,5,6].map(function (i) { return '<button type=\"button\" class=\"wiz-step-bar' + (typeof st === 'number' && i <= st ? ' done' : '') + '\" data-act=\"wizJump\" data-step=\"' + i + '\" aria-label=\"' + esc(tr('Go to setup section ','Ir a la sección ')) + i + '\"></button>'; }).join('');"
one(old_steps, new_steps, 'clickable wizard bars')

old_css = """/* ROUND DB · Suggested Goals: no check circle, stable hover, selection via accent border. */
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested{transition:border-color .14s var(--ease),background .14s var(--ease)!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested:hover{transform:none!important;box-shadow:none!important;border-color:color-mix(in srgb,var(--gc) 58%,var(--line2))!important;background:radial-gradient(112px 78px at 100% 0%,color-mix(in srgb,var(--gc) 15%,transparent),transparent 72%),linear-gradient(160deg,var(--raise),var(--panel))!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested.on{border-color:var(--gc)!important;box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--gc) 34%,transparent)!important;background:radial-gradient(126px 88px at 100% 0%,color-mix(in srgb,var(--gc) 22%,transparent),transparent 72%),linear-gradient(160deg,color-mix(in srgb,var(--gc) 7%,var(--raise)),var(--panel))!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested .wiz-goal-board-foot{justify-content:flex-start!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested .wiz-goal-route-chip{max-width:100%!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested .wiz-goal-board-metric strong{max-width:72%!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;line-height:1.15!important;text-wrap:balance}
.modal.wiz.is-goals .wiz-goal-board-grid:has(.wiz-goal-board-card.is-suggested:nth-child(11)){grid-auto-rows:minmax(148px,auto)!important}
"""
new_css = """/* ROUND DB · Suggested Goals: no check circle, stable hover, selection via accent border. */
.modal.wiz.is-goals .wiz-goal-board-grid:has(.wiz-goal-board-card.is-suggested){grid-template-columns:repeat(4,minmax(0,1fr))!important;grid-template-rows:none!important;grid-auto-rows:minmax(184px,auto)!important;align-content:start!important;overflow-y:auto!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested{min-height:184px!important;transition:border-color .14s var(--ease),background .14s var(--ease)!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested:hover{transform:none!important;box-shadow:none!important;border-color:color-mix(in srgb,var(--gc) 58%,var(--line2))!important;background:radial-gradient(112px 78px at 100% 0%,color-mix(in srgb,var(--gc) 15%,transparent),transparent 72%),linear-gradient(160deg,var(--raise),var(--panel))!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested.on{border-color:var(--gc)!important;box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--gc) 34%,transparent)!important;background:radial-gradient(126px 88px at 100% 0%,color-mix(in srgb,var(--gc) 22%,transparent),transparent 72%),linear-gradient(160deg,color-mix(in srgb,var(--gc) 7%,var(--raise)),var(--panel))!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested .wiz-goal-board-foot{min-height:24px!important;margin-top:2px!important;align-items:flex-start!important;justify-content:flex-start!important;overflow:visible!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested .wiz-goal-route-chip{max-width:100%!important;align-items:flex-start!important;line-height:1.2!important;overflow:visible!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested .wiz-goal-route-chip>span{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;line-height:1.2!important;display:block!important}
.modal.wiz.is-goals .wiz-goal-board-card.is-suggested .wiz-goal-board-metric strong{max-width:72%!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;line-height:1.15!important;text-wrap:balance}
@media(max-width:900px){.modal.wiz.is-goals .wiz-goal-board-grid:has(.wiz-goal-board-card.is-suggested){grid-template-columns:repeat(2,minmax(0,1fr))!important;grid-auto-rows:minmax(178px,auto)!important}.modal.wiz.is-goals .wiz-goal-board-card.is-suggested{min-height:178px!important}}
@media(max-width:560px){.modal.wiz.is-goals .wiz-goal-board-grid:has(.wiz-goal-board-card.is-suggested){grid-template-columns:1fr!important;grid-auto-rows:minmax(172px,auto)!important}.modal.wiz.is-goals .wiz-goal-board-card.is-suggested{min-height:172px!important}}
"""
one(old_css, new_css, 'suggested goal sizing')

p.write_text(s, encoding='utf-8')
after = hashlib.sha256(s.encode()).hexdigest()
expected_after = '9938c26069e8799bf8386fcde6a8ed46fff837b9618e3a95840ae52e1b581c96'
if after != expected_after:
    raise SystemExit(f'Unexpected result hash: {after} != {expected_after}')

scripts = re.findall(r'<script(?:\s[^>]*)?>([\s\S]*?)</script>', s, flags=re.I)
if not scripts:
    raise SystemExit('No inline scripts found')
for i, code in enumerate(scripts):
    f = Path('/tmp') / f'tungsten-stepnav-{i}.js'
    f.write_text(code, encoding='utf-8')
    subprocess.run(['node', '--check', str(f)], check=True)

print('Validated SHA-256:', after)
print('Inline JS blocks:', len(scripts))
