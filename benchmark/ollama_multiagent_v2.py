"""Retrieval-aware local Ollama runner for the AEO benchmark.

v2 separates discovery from retrieval: a discovery agent proposes a resource URL,
that URL is fetched and frozen into the evidence bundle before retrieval/metadata/
citation are evaluated. JSON schema failures are retried once and remain recorded.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, re, time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parents[1]
CFG_PATH = ROOT / "benchmark/config.yaml"
BANK = ROOT / "benchmark/query-bank-120.csv"
OUT = ROOT / "benchmark/results"
PORTALS = {
    "worldbank": ("World Bank Open Data", "https://data.worldbank.org/"),
    "who": ("WHO Data", "https://data.who.int/"),
    "cepalstat": ("CEPALSTAT", "https://statistics.cepal.org/portal/cepalstat/"),
    "undata": ("UN Data Commons", "https://unstats.un.org/UNSDWebsite/undatacommons/"),
    "sdg": ("UN SDG Indicators", "https://unstats.un.org/sdgs/dataportal/"),
}
ROLES = ["discovery", "semantic", "retrieval", "metadata", "citation", "judge", "adversarial"]
REQUIRED = {
    "discovery": {"discovered", "best_url", "confidence", "reason"},
    "semantic": {"selected_indicator_description", "correct", "confidence", "reason", "ambiguity_flags"},
    "retrieval": {"retrievable", "value_found", "period_correct", "geography_correct", "unit_correct", "confidence", "reason"},
    "metadata": {"metadata_complete", "fields_missing", "confidence", "reason"},
    "citation": {"citable", "citation_url", "source_named", "evidence_specific", "confidence", "reason"},
    "judge": {"discovery_success", "retrieval_success", "temporal_geographic_correctness", "semantic_correctness", "metadata_correctness", "citation_correctness", "overall_0_100", "decisive_reason"},
    "adversarial": {"attack_found", "severity", "alternative_interpretation", "verdict", "reason"},
}
PROMPTS = {
    "discovery": "Using only the evidence, identify the official resource relevant to the query. Return JSON only: discovered, best_url, confidence, reason. Prefer a specific indicator/series page or official API over a generic homepage when evidence supports it.",
    "semantic": "Using only the evidence, identify the statistically correct series. Consider concept, unit, price basis, frequency, geography, period and interpretation. Return JSON only with the required schema.",
    "retrieval": "Using only the frozen evidence, determine whether the requested value/series can actually be retrieved without guessing. Return JSON only with the required schema. Do not treat a portal homepage as successful retrieval of a specific value.",
    "metadata": "Using only the evidence, validate definition, source, unit, frequency, reference period, dimensions and methodology. Return JSON only with the required schema.",
    "citation": "Using only the evidence, determine whether the requested result can be cited precisely and reproducibly. Return JSON only with the required schema.",
    "judge": "Act as an independent statistical judge. Use only frozen evidence and structured candidate outputs. Do not use the AEO score. Score discovery, actual retrieval, temporal/geographic correctness, semantic correctness, metadata correctness and citation correctness. Return JSON only.",
    "adversarial": "Try to falsify the candidate result using only frozen evidence and the judge result. Look for wrong indicator, unit, price basis, period, geography, unsupported citation or conflation of discovery with retrieval. Return JSON only.",
}

@dataclass
class Evidence:
    portal_id: str
    query_id: str
    urls: list[str]
    pages: list[dict[str, Any]]
    captured_at: str
    sha256: str


def cfg() -> dict[str, Any]:
    return yaml.safe_load(CFG_PATH.read_text(encoding="utf-8"))


def get(url: str, timeout: float = 25, limit: int = 120000) -> tuple[int, str, dict[str, str]]:
    req = Request(url, headers={"User-Agent": "AEO-Agent-Readiness-Benchmark/2.0", "Accept": "text/html,application/json,text/plain,*/*"})
    try:
        with urlopen(req, timeout=timeout) as r:
            b = r.read(limit); h = {k.lower(): v for k, v in r.headers.items()}
            enc = re.search(r"charset=([^;]+)", h.get("content-type", ""), re.I)
            return r.status, b.decode(enc.group(1).strip('"\'') if enc else "utf-8", errors="replace"), h
    except Exception as e:
        return 0, f"FETCH_ERROR: {type(e).__name__}: {e}", {}


def search_web(q: str, limit: int = 8) -> list[str]:
    urls: list[str] = []
    qp = quote_plus(q)
    engines = [
        f"https://www.google.com/search?q={qp}",
        f"https://www.bing.com/search?q={qp}",
        f"https://html.duckduckgo.com/html/?q={qp}",
    ]
    for engine in engines:
        status, text, _ = get(engine, timeout=20, limit=70000)
        if status != 200: continue
        for m in re.findall(r'https?://[^\s"<>]+', text):
            u = m.replace("&amp;", "&").rstrip(".,);'\"")
            host = urlparse(u).netloc.lower()
            if host.startswith("google.") or host.startswith("bing.") or "duckduckgo" in host: continue
            if u not in urls: urls.append(u)
            if len(urls) >= limit: return urls
    return urls


def freeze(row: dict[str, str], refresh: bool = False) -> Evidence:
    OUT.mkdir(parents=True, exist_ok=True)
    cache = OUT / f"evidence_v2_{row['query_id']}_{row['portal_id']}.json"
    if cache.exists() and not refresh: return Evidence(**json.loads(cache.read_text(encoding="utf-8")))
    home = PORTALS[row["portal_id"]][1]
    urls = [home]
    for u in search_web(f"site:{urlparse(home).netloc} {row['query']}"):
        if u not in urls: urls.append(u)
    pages=[]
    for u in urls[:9]:
        s,t,h=get(u); pages.append({"url":u,"status":s,"content_type":h.get("content-type",""),"text":re.sub(r"\s+"," ",t)[:30000]})
    raw=json.dumps(pages,ensure_ascii=False,sort_keys=True).encode("utf-8")
    ev=Evidence(row["portal_id"],row["query_id"],urls,pages,time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),hashlib.sha256(raw).hexdigest())
    cache.write_text(json.dumps(asdict(ev),ensure_ascii=False,indent=2),encoding="utf-8")
    return ev


def add_url(ev: Evidence, url: str, refresh: bool = False) -> Evidence:
    if not url or not url.startswith(("http://", "https://")) or url in ev.urls: return ev
    s,t,h=get(url); ev.urls.append(url); ev.pages.append({"url":url,"status":s,"content_type":h.get("content-type",""),"text":re.sub(r"\s+"," ",t)[:30000]})
    raw=json.dumps(ev.pages,ensure_ascii=False,sort_keys=True).encode("utf-8"); ev.sha256=hashlib.sha256(raw).hexdigest(); return ev


def tags(base: str) -> list[str]:
    s,t,_=get(base.rstrip("/")+"/api/tags",10,200000)
    if s != 200: raise RuntimeError(f"Ollama unavailable at {base}")
    return [m["name"] for m in json.loads(t).get("models",[])]


def choose(tags_: list[str], c: dict[str,Any]) -> dict[str,str]:
    env={r:os.getenv("AEO_MODEL_"+r.upper()) for r in ROLES}; rolecfg=c.get("roles",{})
    priority=[x for w in ("gemma","qwen","llama","mistral","deepseek") for x in tags_ if w in x.lower()]
    pool=list(dict.fromkeys(priority+tags_))
    out={}
    for r in ROLES:
        req=env.get(r) or rolecfg.get(r)
        if req and req != "auto":
            if req not in tags_: raise RuntimeError(f"Model {req} for {r} is not installed")
            out[r]=req
        elif r=="retrieval": out[r]=next((x for x in pool if "qwen" in x.lower()),pool[0])
        else: out[r]=next((x for x in pool if "gemma" in x.lower()),pool[0])
    return out


def call(base: str, model: str, system: str, user: str, timeout: float, temp: float) -> dict[str,Any]:
    payload={"model":model,"stream":False,"format":"json","options":{"temperature":temp},"messages":[{"role":"system","content":system},{"role":"user","content":user}]}
    started=time.perf_counter()
    try:
        req=Request(base.rstrip("/")+"/api/chat",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
        with urlopen(req,timeout=timeout) as r: data=json.loads(r.read().decode())
    except Exception as e:
        return {"model":model,"ok":False,"error":f"{type(e).__name__}: {e}","elapsed_seconds":round(time.perf_counter()-started,3),"json":None}
    text=data.get("message",{}).get("content","")
    try: parsed=json.loads(text); err=None
    except Exception as e: parsed=None; err=str(e)
    return {"model":model,"ok":True,"text":text,"json":parsed,"parse_error":err,"elapsed_seconds":round(time.perf_counter()-started,3)}


def valid(role: str, obj: Any) -> tuple[bool,str|None]:
    if not isinstance(obj,dict): return False,"response_not_object"
    missing=sorted(REQUIRED[role]-set(obj)); return (False,"missing_keys:"+",".join(missing)) if missing else (True,None)


def prompt(ev: Evidence, query: str, extra: str = "", max_chars: int = 20000) -> str:
    pages="\n\n---\n\n".join(f"URL: {p['url']}\nSTATUS: {p['status']}\nCONTENT-TYPE: {p['content_type']}\nTEXT:\n{p['text']}" for p in ev.pages)
    return (f"QUERY: {query}\n\nFROZEN EVIDENCE:\n{pages}\n\n{extra}")[:max_chars]


def ask(role: str, base: str, model: str, ev: Evidence, row: dict[str,str], c: dict[str,Any], extra: str = "") -> dict[str,Any]:
    timeout=float(c["ollama"].get("timeout_seconds",180)); temp=float(c["ollama"].get("temperature",0.0)); maxc=int(c["ollama"].get("max_context_chars",20000))
    ans=call(base,model,PROMPTS[role],prompt(ev,row["query"],extra,maxc),timeout,temp); ok,err=valid(role,ans.get("json")); ans["schema_valid"]=ok; ans["schema_error"]=err
    if not ok:
        retry_system=PROMPTS[role]+" IMPORTANT: output exactly one JSON object, no markdown, no commentary, with every required key present and JSON booleans/null where appropriate."
        retry=call(base,model,retry_system,prompt(ev,row["query"],extra,8000),timeout,temp); rok,rerr=valid(role,retry.get("json")); retry["schema_valid"]=rok; retry["schema_error"]=rerr; ans["retry"]=retry
        if rok: return {**retry,"initial_failed":True,"initial_error":err}
    return ans


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--base",default=os.getenv("OLLAMA_HOST","http://127.0.0.1:11434")); ap.add_argument("--max-queries",type=int); ap.add_argument("--repeats",type=int,default=1); ap.add_argument("--refresh-evidence",action="store_true"); args=ap.parse_args()
    c=cfg(); rows=list(csv.DictReader(BANK.open(encoding="utf-8"))); tags_=tags(args.base); models=choose(tags_,c); OUT.mkdir(parents=True,exist_ok=True)
    manifest={"runner":"v2","started_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"ollama":args.base,"models_available":tags_,"role_models":models,"repeats":args.repeats}
    (OUT/"run_manifest_v2.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    rows=rows[:args.max_queries] if args.max_queries else rows; results=[]
    for i,row in enumerate(rows,1):
        ev=freeze(row,args.refresh_evidence); discovery=ask("discovery",args.base,models["discovery"],ev,row,c); d=discovery.get("json") if discovery.get("schema_valid") else {}
        candidate=d.get("best_url") if isinstance(d,dict) else None
        ev=add_url(ev,candidate)
        prior={"discovery":d or {"schema_error":discovery.get("schema_error")}}
        for role in ["semantic","retrieval","metadata","citation"]:
            ans=ask(role,args.base,models[role],ev,row,c,json.dumps(prior,ensure_ascii=False,indent=2)); result_json=ans.get("json") if ans.get("schema_valid") else {"schema_error":ans.get("schema_error")}; prior[role]=result_json
            if role not in prior: prior[role]=result_json
        judge=ask("judge",args.base,models["judge"],ev,row,c,"CANDIDATE OUTPUTS:\n"+json.dumps(prior,ensure_ascii=False,indent=2)); prior["judge"]=judge.get("json") if judge.get("schema_valid") else {"schema_error":judge.get("schema_error")}
        adv=ask("adversarial",args.base,models["adversarial"],ev,row,c,"JUDGE RESULT:\n"+json.dumps(prior.get("judge",{}),ensure_ascii=False,indent=2)); prior["adversarial"]=adv.get("json") if adv.get("schema_valid") else {"schema_error":adv.get("schema_error")}
        result={"query":row,"repeat":1,"evidence_sha256":ev.sha256,"agents":{k: v for k,v in [("discovery",discovery),("semantic",ask if False else {}),("retrieval",{}),("metadata",{}),("citation",{}),("judge",judge),("adversarial",adv)]},"candidate_url":candidate}
        # Recover the saved structured agent outputs from prior; keep raw calls in a compact form below.
        for role in ["semantic","retrieval","metadata","citation"]:
            result["agents"][role]={"model":models[role],"json":prior.get(role),"schema_valid":not (isinstance(prior.get(role),dict) and "schema_error" in prior.get(role,{}))}
        results.append(result); print(f"[{i}/{len(rows)}] {row['query_id']} {row['portal_id']} repeat=1",flush=True)
    (OUT/"results_v2.jsonl").write_text("\n".join(json.dumps(r,ensure_ascii=False) for r in results)+"\n",encoding="utf-8")
    print(json.dumps({"runner":"v2","completed":len(results),"models":models,"results":str(OUT/"results_v2.jsonl")},ensure_ascii=False,indent=2))

if __name__ == "__main__": main()
