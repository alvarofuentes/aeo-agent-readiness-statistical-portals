"""Local macOS runner for the multi-agent AEO benchmark.

Requirements: Python 3.11+, Ollama running on localhost. Optional: playwright.
The runner freezes web evidence per query, then sends the same evidence to
specialised local Ollama agents. It never fabricates an agent result.
"""
from __future__ import annotations
import csv, json, os, re, sys, time, hashlib
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "benchmark" / "config.yaml"
BANK = ROOT / "benchmark" / "query_bank_120.csv"
OUT = ROOT / "benchmark" / "results"

PORTALS = {
    "worldbank": ("World Bank Open Data", "https://data.worldbank.org/"),
    "who": ("WHO Data", "https://data.who.int/"),
    "cepalstat": ("CEPALSTAT", "https://statistics.cepal.org/portal/cepalstat/"),
    "undata": ("UN Data Commons", "https://unstats.un.org/UNSDWebsite/undatacommons/"),
    "sdg": ("UN SDG Indicators", "https://unstats.un.org/sdgs/dataportal/"),
}

ROLE_PROMPTS = {
    "discovery": "Determine whether the supplied evidence lets an AI agent discover the official portal/resource relevant to the query. Return JSON with discovered, best_url, confidence, reason.",
    "semantic": "Identify the statistically correct indicator/series among candidates. Focus on concept, unit, price basis, frequency, geography, period and meaning. Return JSON with selected_indicator_description, correct, confidence, reason, ambiguity_flags.",
    "retrieval": "Check whether the supplied evidence contains enough information to retrieve the requested value/series without guessing. Return JSON with retrievable, value_found, period_correct, geography_correct, unit_correct, confidence, reason.",
    "metadata": "Validate the statistical metadata needed for a rigorous answer: definition, source, unit, frequency, reference period, dimensions and methodological notes. Return JSON with metadata_complete, fields_missing, confidence, reason.",
    "citation": "Check whether a user could cite the evidence precisely and reproducibly. Return JSON with citable, citation_url, source_named, evidence_specific, confidence, reason.",
    "judge": "Act as the independent statistical judge. Score the candidate result only from evidence, not from the AEO technical score. Return JSON with discovery_success, retrieval_success, temporal_geographic_correctness, semantic_correctness, metadata_correctness, citation_correctness, overall_0_100, decisive_reason.",
    "adversarial": "Try to falsify the candidate answer. Look for wrong indicator, wrong unit, wrong price basis, wrong period, wrong geography, hidden JS dependence, non-authoritative source, stale page, or unsupported citation. Return JSON with attack_found, severity, alternative_interpretation, verdict, reason.",
}

@dataclass
class Evidence:
    portal_id: str
    query_id: str
    urls: list[str]
    pages: list[dict]
    captured_at: str
    sha256: str


def http_get(url: str, timeout=25, max_bytes=120000) -> tuple[int, str, dict[str,str]]:
    req = Request(url, headers={"User-Agent":"AEO-Agent-Readiness-Benchmark/1.0", "Accept":"text/html,application/json,text/plain,*/*"})
    try:
        with urlopen(req, timeout=timeout) as r:
            body = r.read(max_bytes)
            headers = {k.lower(): v for k,v in r.headers.items()}
            enc = "utf-8"
            m = re.search(r"charset=([^;]+)", headers.get("content-type", ""), re.I)
            if m: enc = m.group(1).strip('"\'')
            return r.status, body.decode(enc, errors="replace"), headers
    except Exception as e:
        return 0, f"FETCH_ERROR: {type(e).__name__}: {e}", {}


def search_web(query: str, limit=5) -> list[str]:
    """Best-effort public search. Falls back to no results; direct portal URL is always retained."""
    urls=[]
    q=quote_plus(query)
    for engine in [f"https://www.google.com/search?q={q}", f"https://www.bing.com/search?q={q}"]:
        status,text,_=http_get(engine, timeout=20, max_bytes=60000)
        if not text or status < 200: continue
        # Extract absolute http(s) links conservatively; reject search-engine/self links.
        for m in re.findall(r'https?://[^\s"<>]+', text):
            u=m.replace('&amp;','&').rstrip('.,);')
            host=urlparse(u).netloc.lower()
            if host in {"www.google.com","google.com","www.bing.com","bing.com"}: continue
            if u not in urls: urls.append(u)
            if len(urls)>=limit: return urls
    return urls


def evidence_for(row: dict, force_refresh=False) -> Evidence:
    OUT.mkdir(parents=True, exist_ok=True)
    cache=OUT/f"evidence_{row['query_id']}_{row['portal_id']}.json"
    if cache.exists() and not force_refresh:
        return Evidence(**json.loads(cache.read_text(encoding="utf-8")))
    portal_name, home = PORTALS[row["portal_id"]]
    urls=[home]
    found=search_web(f"site:{urlparse(home).netloc} {row['query']}", limit=6)
    for u in found:
        if u not in urls: urls.append(u)
    pages=[]
    for u in urls[:7]:
        status,text,headers=http_get(u)
        text=re.sub(r"\s+"," ",text)[:30000]
        pages.append({"url":u,"status":status,"content_type":headers.get("content-type",""),"text":text})
    raw=json.dumps(pages,ensure_ascii=False,sort_keys=True).encode()
    ev=Evidence(row["portal_id"],row["query_id"],urls,[p for p in pages],time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),hashlib.sha256(raw).hexdigest())
    cache.write_text(json.dumps(asdict(ev),ensure_ascii=False,indent=2),encoding="utf-8")
    return ev


def ollama_tags(base: str) -> list[str]:
    status,text,_=http_get(base.rstrip("/")+"/api/tags",timeout=10,max_bytes=200000)
    if status != 200: raise RuntimeError("Ollama is not reachable at "+base)
    data=json.loads(text); return [m["name"] for m in data.get("models",[])]


def choose_models(tags: list[str]) -> dict[str,str]:
    env={r:os.getenv("AEO_MODEL_"+r.upper()) for r in ROLE_PROMPTS}
    fallback=[]
    for wanted in ["gemma","qwen","llama","mistral","deepseek"]:
        fallback += [t for t in tags if wanted in t.lower()]
    fallback += tags
    fallback=list(dict.fromkeys(fallback))
    if not fallback: raise RuntimeError("No Ollama models installed")
    chosen={}
    for role in ROLE_PROMPTS:
        if env.get(role): chosen[role]=env[role]
        elif role in {"semantic","judge","adversarial"}:
            chosen[role]=next((x for x in fallback if "gemma" in x.lower()), fallback[0])
        elif role=="retrieval":
            chosen[role]=next((x for x in fallback if "qwen" in x.lower()), fallback[0])
        else:
            chosen[role]=fallback[0]
    return chosen


def ollama_chat(base: str, model: str, system: str, user: str, temperature=0.0, timeout=180) -> dict:
    payload=json.dumps({"model":model,"stream":False,"options":{"temperature":temperature},"messages":[{"role":"system","content":system},{"role":"user","content":user}]}).encode()
    req=Request(base.rstrip("/")+"/api/chat",data=payload,headers={"Content-Type":"application/json"})
    with urlopen(req,timeout=timeout) as r:
        data=json.loads(r.read().decode("utf-8"))
    text=data.get("message",{}).get("content","")
    m=re.search(r"\{.*\}",text,re.S)
    parsed=None
    if m:
        try: parsed=json.loads(m.group(0))
        except Exception: parsed={"raw":text,"parse_error":True}
    return {"model":model,"text":text,"json":parsed}


def evidence_prompt(ev: Evidence, query: str) -> str:
    chunks=[]
    for p in ev.pages:
        chunks.append(f"URL: {p['url']}\nSTATUS: {p['status']}\nCONTENT-TYPE: {p['content_type']}\nTEXT:\n{p['text']}")
    return f"QUERY: {query}\n\nFROZEN WEB EVIDENCE (do not browse outside it):\n"+"\n\n---\n\n".join(chunks)


def run_one(base,row,ev,models,temperature):
    user=evidence_prompt(ev,row["query"])
    out={"query":row,"evidence_sha256":ev.sha256,"agents":{}}
    prior={}
    for role in ["discovery","semantic","retrieval","metadata","citation","judge","adversarial"]:
        context=user+"\n\nPREVIOUS AGENT OUTPUTS:\n"+json.dumps(prior,ensure_ascii=False,indent=2)
        ans=ollama_chat(base,models[role],ROLE_PROMPTS[role],context,temperature=temperature)
        out["agents"][role]=ans
        prior[role]=ans.get("json") or ans.get("text")
    return out


def flatten(result: dict) -> dict:
    a=result["agents"]
    j=a.get("judge",{}).get("json") or {}
    adv=a.get("adversarial",{}).get("json") or {}
    q=result["query"]
    return {"query_id":q["query_id"],"portal_id":q["portal_id"],"stratum":q["stratum"],"query":q["query"],
            "evidence_sha256":result["evidence_sha256"],"overall_0_100":j.get("overall_0_100"),
            "discovery_success":j.get("discovery_success"),"retrieval_success":j.get("retrieval_success"),
            "temporal_geographic_correctness":j.get("temporal_geographic_correctness"),
            "semantic_correctness":j.get("semantic_correctness"),"metadata_correctness":j.get("metadata_correctness"),
            "citation_correctness":j.get("citation_correctness"),"adversarial_verdict":adv.get("verdict"),
            "adversarial_severity":adv.get("severity")}


def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--base",default=os.getenv("OLLAMA_HOST","http://127.0.0.1:11434")); ap.add_argument("--repeats",type=int,default=3); ap.add_argument("--refresh-evidence",action="store_true"); ap.add_argument("--max-queries",type=int); args=ap.parse_args()
    # Query bank generation is intentionally local and deterministic.
    if not BANK.exists():
        import subprocess; subprocess.check_call([sys.executable,str(ROOT/"benchmark"/"query_bank.py")])
    rows=list(csv.DictReader(BANK.open(encoding="utf-8")))
    if args.max_queries: rows=rows[:args.max_queries]
    tags=ollama_tags(args.base); models=choose_models(tags)
    OUT.mkdir(parents=True,exist_ok=True)
    manifest={"started_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"ollama":args.base,"models_available":tags,"role_models":models,"repeats":args.repeats,"n_queries":len(rows),"n_executions":len(rows)*args.repeats}
    (OUT/"run_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    jsonl=OUT/"results.jsonl"; csvp=OUT/"results.csv"
    flat=[]
    for i,row in enumerate(rows,1):
        ev=evidence_for(row,args.refresh_evidence)
        for rep in range(1,args.repeats+1):
            result=run_one(args.base,row,ev,models,0.0)
            result["repeat"]=rep
            with jsonl.open("a",encoding="utf-8") as f: f.write(json.dumps(result,ensure_ascii=False)+"\n")
            r=flatten(result); r["repeat"]=rep; flat.append(r)
            print(f"[{i}/{len(rows)}] {row['query_id']} {row['portal_id']} repeat={rep}",flush=True)
    fields=list(flat[0].keys()) if flat else []
    with csvp.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(flat)
    print(json.dumps({"completed":len(flat),"results":str(csvp),"models":models},ensure_ascii=False,indent=2))

if __name__=="__main__": main()
