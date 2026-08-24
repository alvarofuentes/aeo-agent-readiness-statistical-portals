#!/usr/bin/env python3
"""Build a static, read-only HTML viewer for model visibility evaluations.

The viewer combines the final evidence runs without changing them.  It embeds
the questions, candidates, normalized answers and model_raw payloads, while
linking back to the original JSONL/model/API evidence files on disk.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    REPO
    / "benchmark/results/fresh/e2e_undata-sdg-30x2x3-20260823-v5/editorial"
    / "model_response_viewer.html"
)

DEFAULT_SOURCES = [
    {
        "label": "CEPALSTAT + World Bank",
        "run": REPO / "benchmark/results/fresh/e2e_cepalstat-worldbank-30x2x3-20260823-v12",
        "portals": {"cepalstat", "worldbank"},
    },
    {
        "label": "WHO",
        "run": REPO / "benchmark/results/fresh/e2e_who-30x1x3-20260823-v4",
        "portals": {"who"},
    },
    {
        "label": "UNData + SDG",
        "run": REPO / "benchmark/results/fresh/e2e_undata-sdg-30x2x3-20260823-v5",
        "portals": {"undata", "sdg"},
    },
]


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def rel_link(path: Path, html_parent: Path) -> str | None:
    if not path.exists():
        return None
    return os.path.relpath(path, html_parent).replace(os.sep, "/")


def status_label(row: dict[str, Any], model: dict[str, Any]) -> tuple[str, str]:
    selection = model.get("selection") or {}
    if selection.get("error"):
        return "RAW NO PARSEABLE", "fail"
    if row.get("selection_error"):
        return "ERROR DE SELECCIÓN", "fail"
    if not row.get("model_ok", True):
        return "MODELO SIN RESPUESTA", "fail"
    if row.get("selection_status") == "PASS" and row.get("e2e_status") == "PASS":
        return "PASS", "pass"
    if row.get("selection_status") == "PASS":
        return row.get("e2e_status") or "REVISAR", "warn"
    return row.get("selection_status") or "REVISAR", "warn"


def build_rows(html_parent: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in DEFAULT_SOURCES:
        run: Path = source["run"]
        result_path = run / "results.jsonl"
        model_dir = run / "evidence/models"
        if not result_path.exists():
            continue
        for line in result_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            portal = row.get("portal_id", "")
            if portal not in source["portals"]:
                continue
            execution_id = row.get("execution_id", "")
            model_path = model_dir / f"{execution_id}.json"
            model = read_json(model_path, {}) or {}
            selection = model.get("selection") or {}
            selection_data = selection.get("data") or {}
            model_raw = selection_data.get("model_raw")
            candidates = model.get("candidates") or []
            if not candidates:
                candidate = row.get("candidate")
                candidates = ([candidate] if candidate else []) + (row.get("near_matches") or [])
            selected_id = (row.get("candidate") or {}).get("id")
            if not selected_id:
                selected_id = selection_data.get("candidate_id")
            api_links = []
            for call in row.get("calls") or []:
                raw_path = call.get("raw_path")
                raw_abs = run / raw_path if raw_path else None
                api_links.append(
                    {
                        "url": call.get("url"),
                        "status": call.get("status"),
                        "elapsed_seconds": call.get("elapsed_seconds"),
                        "raw_link": rel_link(raw_abs, html_parent) if raw_abs else None,
                    }
                )
            label, status_class = status_label(row, model)
            rows.append(
                {
                    "id": execution_id,
                    "template_id": row.get("fresh_template_id") or row.get("source_template_id"),
                    "portal": portal,
                    "repeat": row.get("repeat"),
                    "stratum": row.get("stratum"),
                    "question": row.get("query"),
                    "model": row.get("model"),
                    "endpoint": row.get("model_endpoint"),
                    "selection_status": row.get("selection_status"),
                    "e2e_status": row.get("e2e_status"),
                    "status_label": label,
                    "status_class": status_class,
                    "selection_error": row.get("selection_error") or selection.get("error"),
                    "selection_failure_class": row.get("selection_failure_class"),
                    "candidate_id": selected_id,
                    "candidate": row.get("candidate"),
                    "candidates": candidates,
                    "near_matches": row.get("near_matches") or [],
                    "query_rewrite": selection_data.get("query_rewrite"),
                    "reason": selection_data.get("reason"),
                    "model_raw": model_raw,
                    "model_raw_saved": bool(model_raw),
                    "model_attempts": selection.get("attempts"),
                    "retrieval_status": row.get("retrieval_status"),
                    "rows_returned": row.get("rows_returned"),
                    "value_found": row.get("value_found"),
                    "values": row.get("values") or [],
                    "citation_url": row.get("citation_url"),
                    "api_links": api_links,
                    "model_link": rel_link(model_path, html_parent),
                    "results_link": rel_link(result_path, html_parent),
                    "source_label": source["label"],
                }
            )
    rows.sort(key=lambda r: (r["portal"], r["template_id"] or "", r["repeat"] or 0))
    return rows


def render_html(rows: list[dict[str, Any]], output: Path) -> str:
    portals = sorted({r["portal"] for r in rows})
    model_count = sum(1 for r in rows if r["model_raw_saved"])
    issue_count = sum(1 for r in rows if r["status_class"] != "pass" or not r["model_raw_saved"])
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows": rows,
        "portals": portals,
        "stats": {
            "total": len(rows),
            "modelRaw": model_count,
            "modelRawMissing": len(rows) - model_count,
            "issues": issue_count,
        },
    }
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return HTML_TEMPLATE.replace("__PAYLOAD__", data_json)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else REPO / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = build_rows(output.parent)
    output.write_text(render_html(rows, output), encoding="utf-8")
    print(f"Generated {output} with {len(rows)} rows")


HTML_TEMPLATE = r'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Visibilidad E2E · visor de respuestas</title>
  <style>
    :root {
      --ink:#14213d; --muted:#667085; --line:#e7eaf0; --soft:#f7f8fb;
      --teal:#0e9f8b; --teal-soft:#e5f6f2; --amber:#bd7b08; --amber-soft:#fff5dc;
      --red:#bf3b4d; --red-soft:#fff0f2; --blue:#3167d8; --shadow:0 18px 55px rgba(20,33,61,.10);
    }
    *{box-sizing:border-box} body{margin:0;background:#f8fafc;color:var(--ink);font:14px/1.45 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
    button,input,select{font:inherit} button{cursor:pointer;border:0}
    .shell{min-height:100vh;display:grid;grid-template-columns:252px 1fr}
    aside{background:#101a32;color:#dbe5fb;padding:27px 18px;display:flex;flex-direction:column;gap:26px;position:sticky;top:0;height:100vh}
    .brand{display:flex;gap:11px;align-items:center}.mark{width:32px;height:32px;border-radius:10px;background:linear-gradient(135deg,#1cc5af,#3184ff);display:grid;place-items:center;color:#fff;font-weight:800}.brand b{font-size:14px;letter-spacing:.02em}.brand span{font-size:11px;color:#9eb0d1;display:block;margin-top:2px}
    .side-copy{font-size:12px;color:#9eb0d1;line-height:1.55;margin:0 4px}.side-label{text-transform:uppercase;font-size:10px;letter-spacing:.12em;color:#7284a9;margin:0 4px 9px}
    .legend{display:grid;gap:9px}.legend-row{display:flex;align-items:center;gap:8px;color:#c4d0e8;font-size:12px}.dot{width:8px;height:8px;border-radius:50%;display:inline-block}.dot.pass{background:#20c39a}.dot.warn{background:#f3ba56}.dot.fail{background:#eb6c7a}
    .side-footer{margin-top:auto;font-size:11px;color:#7386ac;line-height:1.6}.side-footer code{font-size:10px;color:#a6b8da}
    main{min-width:0;padding:29px 38px 50px}.topline{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;margin-bottom:25px}.eyebrow{font-size:11px;color:var(--teal);font-weight:750;letter-spacing:.12em;text-transform:uppercase}.title{font-size:29px;letter-spacing:-.035em;margin:5px 0 5px}.subtitle{margin:0;color:var(--muted);max-width:760px}.top-actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}.btn{background:#fff;border:1px solid var(--line);border-radius:9px;padding:9px 12px;color:var(--ink);font-weight:650;box-shadow:0 2px 5px rgba(20,33,61,.03)}.btn:hover{border-color:#bcc6d8;background:#fcfdff}.btn.primary{background:var(--ink);color:#fff;border-color:var(--ink)}
    .stats{display:grid;grid-template-columns:repeat(4,minmax(130px,1fr));gap:12px;margin-bottom:20px}.stat{background:#fff;border:1px solid var(--line);border-radius:14px;padding:15px 16px;box-shadow:0 5px 18px rgba(20,33,61,.035)}.stat-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.stat-value{font-size:25px;font-weight:760;letter-spacing:-.04em;margin-top:3px}.stat-note{font-size:11px;color:var(--muted);margin-top:2px}.stat.alert .stat-value{color:var(--red)}
    .toolbar{background:#fff;border:1px solid var(--line);border-radius:14px;padding:13px;display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-bottom:14px;box-shadow:0 5px 18px rgba(20,33,61,.035)}.search{flex:1 1 290px;position:relative}.search input{width:100%;padding:10px 12px 10px 35px;border:1px solid var(--line);border-radius:9px;outline:none}.search input:focus,.control:focus{border-color:#8bb9ff;box-shadow:0 0 0 3px rgba(49,103,216,.11)}.search-icon{position:absolute;left:12px;top:9px;color:#8b98ac}.control{border:1px solid var(--line);background:#fff;border-radius:9px;padding:10px 29px 10px 10px;outline:none;color:var(--ink)}.check{display:flex;gap:7px;align-items:center;color:var(--muted);font-size:12px;padding:0 4px;white-space:nowrap}.count{margin-left:auto;color:var(--muted);font-size:12px}
    .modebar{display:flex;align-items:center;gap:8px;margin:16px 0 9px}.modebtn{background:transparent;border:1px solid transparent;border-radius:8px;padding:7px 10px;color:var(--muted);font-weight:650}.modebtn.active{background:#eaf0ff;border-color:#ccdcff;color:var(--blue)}
    .table-wrap{background:#fff;border:1px solid var(--line);border-radius:14px;overflow:auto;box-shadow:0 5px 18px rgba(20,33,61,.035)}table{border-collapse:collapse;width:100%;min-width:930px}th{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#7d899c;text-align:left;padding:13px 15px;background:#fbfcfe;border-bottom:1px solid var(--line);white-space:nowrap}td{padding:12px 15px;border-bottom:1px solid #f0f2f6;vertical-align:top}tr:last-child td{border-bottom:0}tbody tr{cursor:pointer}tbody tr:hover{background:#fbfdff}.q{font-weight:640;max-width:385px}.sub{font-size:11px;color:var(--muted);margin-top:3px}.portal{font-weight:720;color:#364766}.id{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;color:#6e7c93}.badge{display:inline-flex;align-items:center;border-radius:999px;padding:4px 8px;font-size:10px;font-weight:760;letter-spacing:.04em;white-space:nowrap}.badge.pass{background:var(--teal-soft);color:#087968}.badge.warn{background:var(--amber-soft);color:#986007}.badge.fail{background:var(--red-soft);color:#a42b3d}.saved{color:#118e7a;font-weight:700;font-size:11px}.not-saved{color:#b84756;font-weight:700;font-size:11px}
    .empty{padding:36px;text-align:center;color:var(--muted)}
    .overlay{position:fixed;inset:0;background:rgba(11,18,35,.38);backdrop-filter:blur(3px);display:none;z-index:5}.overlay.open{display:block}.drawer{position:absolute;right:0;top:0;height:100%;width:min(760px,96vw);background:#fff;box-shadow:-20px 0 70px rgba(12,22,44,.22);overflow:auto}.drawer-head{padding:22px 25px 18px;border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(255,255,255,.96);backdrop-filter:blur(10px);z-index:2}.drawer-title{font-size:20px;line-height:1.25;letter-spacing:-.025em;margin:7px 40px 7px 0}.drawer-meta{display:flex;gap:7px;flex-wrap:wrap;align-items:center;color:var(--muted);font-size:12px}.close{position:absolute;right:20px;top:20px;background:#f1f3f7;color:#52617a;border-radius:50%;width:30px;height:30px;font-size:20px;line-height:1}.drawer-body{padding:20px 25px 44px}.section{margin-bottom:22px}.section h3{font-size:11px;text-transform:uppercase;letter-spacing:.11em;color:#7b879a;margin:0 0 10px}.answer-card{border:1px solid #d9e3f2;border-radius:12px;padding:14px;background:#fbfdff}.answer-title{display:flex;justify-content:space-between;gap:14px;align-items:flex-start}.answer-name{font-size:16px;font-weight:750}.answer-id{font-family:ui-monospace,monospace;color:var(--blue);font-size:12px}.kv{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 22px;margin-top:12px}.kv div{font-size:12px}.kv label{display:block;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.07em;margin-bottom:2px}.kv span{font-weight:620}.copy{color:#3f4d66;white-space:pre-wrap}.candidate-list{display:grid;gap:7px}.candidate{display:grid;grid-template-columns:25px 1fr auto;gap:9px;align-items:start;padding:10px;border:1px solid var(--line);border-radius:9px}.candidate.selected{border-color:#9bd8ca;background:#f5fcfa}.candidate-num{font-size:11px;color:var(--muted);padding-top:2px}.candidate-name{font-size:12px;font-weight:650}.candidate-meta{font-size:10px;color:var(--muted);margin-top:3px}.pre{background:#101a32;color:#dce7fb;border-radius:11px;padding:14px;overflow:auto;max-height:280px;font:11px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap}.muted-box{background:#fff7e6;border:1px solid #f2d58b;color:#80580b;border-radius:10px;padding:11px 12px;font-size:12px}.links{display:grid;gap:8px}.link-row{display:flex;justify-content:space-between;gap:12px;align-items:center;border:1px solid var(--line);padding:9px 11px;border-radius:9px;font-size:12px}.link-row a{color:var(--blue);font-weight:650;text-decoration:none}.link-row a:hover{text-decoration:underline}
    .compare{display:none;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:12px}.compare.show{display:grid}.compare-card{background:#fff;border:1px solid var(--line);border-radius:13px;padding:14px;min-height:168px}.compare-card h4{margin:0 0 8px;font-size:13px}.compare-q{font-size:11px;color:var(--muted);margin-bottom:11px}.rep{border-top:1px solid #f0f2f6;padding:8px 0;display:flex;justify-content:space-between;gap:8px;align-items:center}.rep:first-of-type{border-top:0}.rep-name{font-size:11px;font-weight:650}.rep-answer{font-size:10px;color:var(--muted);text-align:right;max-width:150px}.hidden{display:none!important}
    @media(max-width:900px){.shell{grid-template-columns:1fr}aside{position:relative;height:auto;padding:18px;gap:14px}.side-footer{display:none}.legend{display:flex;gap:14px}.stats{grid-template-columns:repeat(2,1fr)}main{padding:22px 16px 38px}.topline{display:block}.top-actions{justify-content:flex-start;margin-top:14px}.title{font-size:25px}.kv{grid-template-columns:1fr}}
  </style>
</head>
<body>
<div class="shell">
  <aside>
    <div class="brand"><div class="mark">A</div><div><b>Visibility audit</b><span>visor E2E de modelos</span></div></div>
    <p class="side-copy">Una lectura trazable de cómo el modelo interpreta cada pregunta, qué alternativas recibe y qué respuesta devuelve el portal.</p>
    <div><div class="side-label">Estados</div><div class="legend"><div class="legend-row"><i class="dot pass"></i>Pass / respuesta recuperada</div><div class="legend-row"><i class="dot warn"></i>Revisar / resultado parcial</div><div class="legend-row"><i class="dot fail"></i>Error / raw ausente</div></div></div>
    <div class="side-footer">Fuente: ejecuciones E2E finales<br><code id="generated"></code><br><br>Los JSON originales no se modifican.</div>
  </aside>
  <main>
    <div class="topline"><div><div class="eyebrow">Auditoría reproducible</div><h1 class="title">Preguntas, alternativas y respuestas</h1><p class="subtitle">Explora la decisión del modelo y la evidencia de recuperación de cada consulta, con comparación entre repeticiones.</p></div><div class="top-actions"><button class="btn" id="exportCsv">Exportar CSV</button><button class="btn" id="exportJson">Exportar JSON</button><button class="btn primary" id="reset">Limpiar filtros</button></div></div>
    <div class="stats"><div class="stat"><div class="stat-label">Ejecuciones</div><div class="stat-value" id="totalStat">—</div><div class="stat-note">preguntas × portales × repeticiones</div></div><div class="stat"><div class="stat-label">Raw del modelo</div><div class="stat-value" id="rawStat">—</div><div class="stat-note">respuesta cruda disponible</div></div><div class="stat"><div class="stat-label">Revisión</div><div class="stat-value" id="issueStat">—</div><div class="stat-note">errores o evidencia incompleta</div></div><div class="stat"><div class="stat-label">Portales</div><div class="stat-value" id="portalStat">—</div><div class="stat-note">en el paquete consolidado</div></div></div>
    <div class="toolbar"><div class="search"><span class="search-icon">⌕</span><input id="search" placeholder="Buscar pregunta, candidato, ID o respuesta…"></div><select class="control" id="portal"><option value="">Todos los portales</option></select><select class="control" id="status"><option value="">Todos los estados</option><option value="pass">Pass</option><option value="warn">Revisar</option><option value="fail">Error</option></select><select class="control" id="stratum"><option value="">Todos los estratos</option></select><select class="control" id="repeat"><option value="">Todas las repeticiones</option><option value="1">Repetición 1</option><option value="2">Repetición 2</option><option value="3">Repetición 3</option></select><label class="check"><input type="checkbox" id="issuesOnly"> Sólo revisar</label><span class="count" id="count">—</span></div>
    <div class="modebar"><button class="modebtn active" data-mode="table">Lista de consultas</button><button class="modebtn" data-mode="compare">Comparar repeticiones</button></div>
    <div id="tableView" class="table-wrap"><table><thead><tr><th>ID / portal</th><th>Pregunta</th><th>Selección</th><th>Estado</th><th>Modelo</th><th>Evidencia</th></tr></thead><tbody id="tbody"></tbody></table><div class="empty hidden" id="empty">No hay consultas que coincidan con los filtros.</div></div>
    <div id="compareView" class="compare"></div>
  </main>
</div>
<div class="overlay" id="overlay"><section class="drawer"><div class="drawer-head"><button class="close" id="close">×</button><div class="eyebrow" id="dEyebrow"></div><h2 class="drawer-title" id="dTitle"></h2><div class="drawer-meta" id="dMeta"></div></div><div class="drawer-body" id="dBody"></div></section></div>
<script>
const PAYLOAD=__PAYLOAD__;
const rows=PAYLOAD.rows;
const $=s=>document.querySelector(s);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pretty=v=>typeof v==='string'?v:JSON.stringify(v,null,2);
$('#generated').textContent=new Date(PAYLOAD.generatedAt).toLocaleString('es-CL',{dateStyle:'medium',timeStyle:'short'});
$('#totalStat').textContent=PAYLOAD.stats.total; $('#rawStat').textContent=`${PAYLOAD.stats.modelRaw}/${PAYLOAD.stats.total}`; $('#issueStat').textContent=PAYLOAD.stats.issues; $('#portalStat').textContent=PAYLOAD.portals.length;
PAYLOAD.portals.forEach(p=>$('#portal').insertAdjacentHTML('beforeend',`<option value="${esc(p)}">${esc(p)}</option>`));
[...new Set(rows.map(r=>r.stratum).filter(Boolean))].sort().forEach(s=>$('#stratum').insertAdjacentHTML('beforeend',`<option value="${esc(s)}">${esc(s)}</option>`));
function filtered(){const q=$('#search').value.toLowerCase().trim(), p=$('#portal').value, st=$('#status').value, str=$('#stratum').value, rep=$('#repeat').value, only=$('#issuesOnly').checked; return rows.filter(r=>{const hay=[r.id,r.portal,r.question,r.candidate_id,r.candidate?.name,r.model_raw,r.query_rewrite,r.reason].filter(Boolean).join(' ').toLowerCase();return(!q||hay.includes(q))&&(!p||r.portal===p)&&(!st||r.status_class===st)&&(!str||r.stratum===str)&&(!rep||String(r.repeat)===rep)&&(!only||(r.status_class!=='pass'||!r.model_raw_saved));});}
function render(){const data=filtered();$('#count').textContent=`${data.length} de ${rows.length}`;const body=$('#tbody');body.innerHTML=data.map(r=>`<tr data-id="${esc(r.id)}"><td><div class="id">${esc(r.id)}</div><div class="portal">${esc(r.portal)}</div><div class="sub">R${esc(r.repeat)} · ${esc(r.stratum)}</div></td><td><div class="q">${esc(r.question)}</div><div class="sub">${esc(r.template_id)}</div></td><td><div class="answer-id">${esc(r.candidate_id||'—')}</div><div class="sub">${esc(r.candidate?.name||'Sin candidato')}</div></td><td><span class="badge ${r.status_class}">${esc(r.status_label)}</span><div class="sub">${esc(r.e2e_status||r.selection_status||'—')}</div></td><td><div class="sub">${esc(r.model||'—')}</div><div class="sub">${esc(r.endpoint||'—')}</div></td><td>${r.model_raw_saved?'<span class="saved">● raw guardado</span>':'<span class="not-saved">● raw ausente</span>'}<div class="sub">${(r.api_links||[]).length} llamada(s) API</div></td></tr>`).join('');$('#empty').classList.toggle('hidden',data.length>0);body.querySelectorAll('tr').forEach(tr=>tr.onclick=()=>openDetail(rows.find(r=>r.id===tr.dataset.id)));}
function openDetail(r){if(!r)return;$('#dEyebrow').textContent=`${r.portal} · repetición ${r.repeat} · ${r.stratum}`;$('#dTitle').textContent=r.question;$('#dMeta').innerHTML=`<span class="badge ${r.status_class}">${esc(r.status_label)}</span><span>${esc(r.id)}</span><span>·</span><span>${esc(r.model||'modelo no informado')}</span>`;const answer=r.candidate;const candidates=r.candidates||[];const answerIsModelSelection=r.selection_status==='PASS'&&!r.selection_error;const answerBadge=answerIsModelSelection?'<span class="badge pass">seleccionado por modelo</span>':'<span class="badge warn">fallback diagnóstico</span>';const api=(r.api_links||[]).map(c=>`<div class="link-row"><span>HTTP ${esc(c.status||'—')} · ${esc(c.elapsed_seconds??'—')} s</span>${c.raw_link?`<a href="${esc(c.raw_link)}" target="_blank">respuesta API ↗</a>`:'<span class="sub">sin archivo raw</span>'}</div>`).join('');$('#dBody').innerHTML=`<div class="section"><h3>Decisión del modelo</h3>${answer?`<div class="answer-card"><div class="answer-title"><div><div class="answer-name">${esc(answer.name||'Candidato preservado')}</div><div class="answer-id">ID ${esc(r.candidate_id)}</div></div>${answerBadge}</div>${!answerIsModelSelection?'<div class="muted-box" style="margin-top:11px">La selección no pasó; este candidato se conserva sólo para diagnóstico y no sustituye la decisión del modelo.</div>':''}<div class="kv"><div><label>Consulta reformulada</label><span>${esc(r.query_rewrite||'—')}</span></div><div><label>Fuente</label><span>${esc(answer.selection_metadata?.source_catalog||r.portal)}</span></div></div></div>`:'<div class="muted-box">El modelo no seleccionó un candidato.</div>'}</div><div class="section"><h3>Alternativas recuperadas</h3><div class="candidate-list">${candidates.length?candidates.map((c,i)=>`<div class="candidate ${String(c.id)===String(r.candidate_id)&&answerIsModelSelection?'selected':''}"><div class="candidate-num">${i+1}</div><div><div class="candidate-name">${esc(c.name||'Sin nombre')}</div><div class="candidate-meta">ID ${esc(c.id||c.indicator_id||'—')} · ${esc(c.selection_metadata?Object.entries(c.selection_metadata).map(([k,v])=>`${k}: ${v}`).join(' · '):'metadatos no disponibles')}</div></div>${String(c.id)===String(r.candidate_id)&&answerIsModelSelection?'<span class="badge pass">OK</span>':''}</div>`).join(''):'<div class="muted-box">No hay alternativas guardadas.</div>'}</div></div><div class="section"><h3>Razonamiento y respuesta cruda</h3>${r.reason?`<div class="copy" style="margin-bottom:10px"><b>Razón registrada:</b> ${esc(r.reason)}</div>`:''}${r.model_raw?`<pre class="pre">${esc(r.model_raw)}</pre>`:`<div class="muted-box">La respuesta cruda no fue guardada. Error registrado: ${esc(r.selection_error||'sin detalle')} · intentos: ${esc(r.model_attempts||'—')}</div>`}</div><div class="section"><h3>Resultado de la consulta al portal</h3><div class="kv"><div><label>Estado recuperación</label><span>${esc(r.retrieval_status||'—')}</span></div><div><label>Valor encontrado</label><span>${esc(String(r.value_found??'—'))}</span></div><div><label>Filas devueltas</label><span>${esc(r.rows_returned??'—')}</span></div><div><label>URL de citación</label><span>${r.citation_url?`<a href="${esc(r.citation_url)}" target="_blank">abrir fuente ↗</a>`:'—'}</span></div></div>${r.values?.length?`<pre class="pre" style="margin-top:12px;max-height:180px">${esc(pretty(r.values))}</pre>`:''}</div><div class="section"><h3>Evidencia y trazabilidad</h3><div class="links"><div class="link-row"><span>JSON de decisión del modelo</span>${r.model_link?`<a href="${esc(r.model_link)}" target="_blank">abrir evidencia ↗</a>`:'<span>no disponible</span>'}</div><div class="link-row"><span>Fila normalizada en results.jsonl</span>${r.results_link?`<a href="${esc(r.results_link)}" target="_blank">abrir archivo ↗</a>`:'<span>no disponible</span>'}</div>${api}</div></div>`;$('#overlay').classList.add('open');}
function renderCompare(){const data=filtered();const groups={};data.forEach(r=>{const k=`${r.portal} · ${r.template_id}`;(groups[k]??=[]).push(r)});const out=$('#compareView');const keys=Object.keys(groups).sort();out.innerHTML=keys.map(k=>{const rs=groups[k].sort((a,b)=>(a.repeat||0)-(b.repeat||0));const q=rs[0]?.question||'';return `<article class="compare-card"><h4>${esc(k)}</h4><div class="compare-q">${esc(q)}</div>${[1,2,3].map(n=>{const r=rs.find(x=>x.repeat===n);return r?`<div class="rep" data-id="${esc(r.id)}"><div><div class="rep-name">Repetición ${n}</div><span class="badge ${r.status_class}">${esc(r.status_label)}</span></div><div class="rep-answer">${esc(r.candidate_id||'sin candidato')}<br>${esc(r.candidate?.name||'')}</div></div>`:`<div class="rep"><div class="rep-name">Repetición ${n}</div><div class="rep-answer">sin registro</div></div>`}).join('')}</article>`}).join('')||'<div class="empty">No hay grupos que coincidan con los filtros.</div>';out.querySelectorAll('.rep[data-id]').forEach(el=>el.onclick=()=>openDetail(rows.find(r=>r.id===el.dataset.id)));}
function switchMode(mode){document.querySelectorAll('.modebtn').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));$('#tableView').classList.toggle('hidden',mode!=='table');$('#compareView').classList.toggle('show',mode==='compare');if(mode==='compare')renderCompare();}
document.querySelectorAll('.toolbar input,.toolbar select').forEach(el=>el.addEventListener('input',()=>{render();if($('#compareView').classList.contains('show'))renderCompare()}));document.querySelectorAll('.modebtn').forEach(b=>b.onclick=()=>switchMode(b.dataset.mode));$('#close').onclick=()=>$('#overlay').classList.remove('open');$('#overlay').onclick=e=>{if(e.target.id==='overlay')$('#overlay').classList.remove('open')};document.addEventListener('keydown',e=>{if(e.key==='Escape')$('#overlay').classList.remove('open')});$('#reset').onclick=()=>{$('#search').value='';$('#portal').value='';$('#status').value='';$('#stratum').value='';$('#repeat').value='';$('#issuesOnly').checked=false;render();if($('#compareView').classList.contains('show'))renderCompare()};
function download(name,text,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;a.click();URL.revokeObjectURL(a.href)}
$('#exportJson').onclick=()=>download('model-response-review.json',JSON.stringify(filtered(),null,2),'application/json');$('#exportCsv').onclick=()=>{const data=filtered(), cols=['id','portal','template_id','repeat','stratum','question','model','candidate_id','status_label','selection_status','e2e_status','model_raw_saved','retrieval_status','value_found','citation_url'];const csv=[cols.join(','),...data.map(r=>cols.map(c=>`"${String(r[c]??'').replace(/"/g,'""')}"`).join(','))].join('\n');download('model-response-review.csv',csv,'text/csv;charset=utf-8')};
render();
</script>
</body>
</html>'''


if __name__ == "__main__":
    main()
