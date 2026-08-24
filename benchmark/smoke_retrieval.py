"""Small retrieval-aware smoke test for the local Ollama AEO benchmark.

This validator intentionally runs a handful of queries only. It separates discovery
from retrieval by fetching the discovery agent's best_url before the retrieval agent
runs. It is not the production benchmark runner.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, re, time
from pathlib import Path
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen
from typing import Any
import yaml

try:
    from .model_policy import allowed_models, assert_allowed_model
except ImportError:  # direct invocation: python benchmark/smoke_retrieval.py
    from model_policy import allowed_models, assert_allowed_model

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"benchmark/config.yaml"
BANK=ROOT/"benchmark/query-bank-120.csv"
OUT=ROOT/"benchmark/results"
PORTALS={
    "worldbank":"https://data.worldbank.org/",
    "who":"https://data.who.int/",
    "cepalstat":"https://statistics.cepal.org/portal/cepalstat/",
    "undata":"https://unstats.un.org/UNSDWebsite/undatacommons/",
    "sdg":"https://unstats.un.org/sdgs/dataportal/",
}
PORTAL_ALLOWED_ROOTS={"worldbank":{"worldbank.org"},"who":{"who.int","azureedge.net"},"cepalstat":{"cepal.org"},"undata":{"unstats.un.org"},"sdg":{"unstats.un.org"}}
ROLES=["discovery","semantic","retrieval","metadata","citation","judge","adversarial"]
SCHEMA={
    "discovery":{"discovered","best_url","confidence","reason"},
    "semantic":{"selected_indicator_description","correct","confidence","reason","ambiguity_flags"},
    "retrieval":{"retrievable","value_found","period_correct","geography_correct","unit_correct","confidence","reason"},
    "metadata":{"metadata_complete","fields_missing","confidence","reason"},
    "citation":{"citable","citation_url","source_named","evidence_specific","confidence","reason"},
    "judge":{"discovery_success","retrieval_success","temporal_geographic_correctness","semantic_correctness","metadata_correctness","citation_correctness","overall_0_100","decisive_reason"},
    "adversarial":{"attack_found","severity","alternative_interpretation","verdict","reason"},
}
PROMPTS={
    "discovery":"Find the official resource relevant to the query in the supplied evidence. Prefer a specific indicator/series/API URL over a generic homepage. Return only a JSON object with the required keys.",
    "semantic":"Select the statistically correct indicator/series from the evidence. Check concept, unit, prices, frequency, geography and period. Return only JSON.",
    "retrieval":"Decide whether the requested value/series is actually present or retrievable from the supplied evidence without guessing. A homepage alone is not retrieval. Return only JSON.",
    "metadata":"Check whether the evidence contains rigorous statistical metadata: definition, source, unit, frequency, period, dimensions and methodology. Return only JSON.",
    "citation":"Check whether the requested result can be cited precisely and reproducibly from the evidence. Return only JSON.",
    "judge":"Independently score the candidate using only frozen evidence and structured outputs. Do not use the technical AEO score. Return only JSON.",
    "adversarial":"Try to falsify the judge result using the frozen evidence. Look for wrong indicator, unit, period, geography, unsupported citation or conflation of discovery and retrieval. Return only JSON.",
}

def get(url:str, timeout:float=20, limit:int=100000):
    req=Request(url,headers={"User-Agent":"AEO-Agent-Readiness-Benchmark/2.1","Accept":"text/html,application/json,text/plain,*/*"})
    try:
        with urlopen(req,timeout=timeout) as r:
            body=r.read(limit); h={k.lower():v for k,v in r.headers.items()}
            enc=re.search(r"charset=([^;]+)",h.get("content-type",""),re.I)
            return r.status,body.decode(enc.group(1).strip('"\'') if enc else "utf-8",errors="replace"),h
    except Exception as e:
        return 0,f"FETCH_ERROR: {type(e).__name__}: {e}",{}

def search(query:str,domain:str,limit:int=6):
    qp=quote_plus(f"site:{domain} {query}"); urls=[]
    for engine in [f"https://www.google.com/search?q={qp}",f"https://www.bing.com/search?q={qp}",f"https://html.duckduckgo.com/html/?q={qp}"]:
        status,text,_=get(engine,timeout=20,limit=70000)
        if status!=200: continue
        for m in re.findall(r'https?://[^\s"<>]+',text):
            u=m.replace("&amp;","&").rstrip(".,);'\""); host=urlparse(u).netloc.lower()
            if any(x in host for x in ["google.","bing.","duckduckgo."]): continue
            host=urlparse(u).hostname.lower().rstrip(".") if urlparse(u).hostname else ""
            root=domain.lower().rstrip(".")
            if (host==root or host.endswith("."+root)) and u not in urls: urls.append(u)
            if len(urls)>=limit: return urls
    return urls

def portal_url_allowed(portal_id:str,url:str)->bool:
    host=urlparse(url).hostname.lower().rstrip(".") if urlparse(url).hostname else ""
    return any(host==root or host.endswith("."+root) for root in PORTAL_ALLOWED_ROOTS[portal_id])

def freeze(row, refresh=False):
    cache=OUT/f"smoke_evidence_{row['query_id']}_{row['portal_id']}.json"; OUT.mkdir(parents=True,exist_ok=True)
    if cache.exists() and not refresh: return json.loads(cache.read_text(encoding="utf-8"))
    home=PORTALS[row["portal_id"]]; urls=[home]+search(row["query"],urlparse(home).netloc)
    pages=[]
    for u in list(dict.fromkeys(urls))[:7]:
        s,t,h=get(u); pages.append({"url":u,"status":s,"content_type":h.get("content-type",""),"text":re.sub(r"\s+"," ",t)[:25000]})
    raw=json.dumps(pages,ensure_ascii=False,sort_keys=True).encode(); ev={"urls":urls,"pages":pages,"sha256":hashlib.sha256(raw).hexdigest(),"captured_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
    cache.write_text(json.dumps(ev,ensure_ascii=False,indent=2),encoding="utf-8"); return ev

def ollama_tags(base):
    s,t,_=get(base.rstrip("/")+"/api/tags",10,200000)
    if s!=200: raise RuntimeError(f"Ollama unavailable: {base}")
    return [m["name"] for m in json.loads(t).get("models",[])]

def choose(tags,cfg):
    tags=allowed_models(tags); env={r:os.getenv("AEO_MODEL_"+r.upper()) for r in ROLES}; out={}; pool=list(dict.fromkeys([x for w in ["gemma","qwen","llama","mistral","deepseek"] for x in tags if w in x.lower()]+tags))
    if not pool: raise RuntimeError("No local model within the <=24B policy is installed")
    for r in ROLES:
        req=env.get(r) or cfg.get("roles",{}).get(r)
        if req and req!="auto": assert_allowed_model(req); out[r]=req
        elif r=="retrieval": out[r]=next((x for x in pool if "qwen" in x.lower()),pool[0])
        else: out[r]=next((x for x in pool if "gemma" in x.lower()),pool[0])
    return out

def call(base,model,system,user,timeout=180,temp=0.0):
    payload={"model":model,"stream":False,"format":"json","options":{"temperature":temp},"messages":[{"role":"system","content":system},{"role":"user","content":user}]}
    started=time.perf_counter()
    try:
        req=Request(base.rstrip("/")+"/api/chat",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
        with urlopen(req,timeout=timeout) as r: data=json.loads(r.read().decode())
    except Exception as e:
        return {"model":model,"ok":False,"json":None,"error":f"{type(e).__name__}: {e}","elapsed_seconds":round(time.perf_counter()-started,3)}
    text=data.get("message",{}).get("content","")
    try: obj=json.loads(text); err=None
    except Exception as e: obj=None; err=str(e)
    return {"model":model,"ok":True,"json":obj,"text":text,"parse_error":err,"elapsed_seconds":round(time.perf_counter()-started,3)}

def ask(role,base,model,ev,query,extra="",max_chars=18000):
    pages="\n\n---\n\n".join(f"URL: {p['url']}\nSTATUS: {p['status']}\nTEXT:\n{p['text']}" for p in ev["pages"])
    user=(f"QUERY: {query}\n\nFROZEN EVIDENCE:\n{pages}\n\n{extra}")[:max_chars]
    ans=call(base,model,PROMPTS[role],user); obj=ans.get("json")
    missing=sorted(SCHEMA[role]-set(obj)) if isinstance(obj,dict) else list(SCHEMA[role])
    if not missing and isinstance(obj,dict):
        bool_keys={"discovery":["discovered"],"semantic":["correct"],"retrieval":["retrievable","value_found","period_correct","geography_correct","unit_correct"],"metadata":["metadata_complete"],"citation":["citable","source_named","evidence_specific"],"adversarial":["attack_found"]}.get(role,[])
        if any(v is not None and not isinstance(obj.get(v),bool) for v in bool_keys): missing=["type_error:boolean"]
        if role in {"discovery","semantic","retrieval","metadata","citation"} and (not isinstance(obj.get("confidence"),(int,float)) or isinstance(obj.get("confidence"),bool) or not 0<=obj.get("confidence",-1)<=1): missing=["type_error:confidence"]
        if role=="judge" and (not isinstance(obj.get("overall_0_100"),(int,float)) or isinstance(obj.get("overall_0_100"),bool) or not 0<=obj.get("overall_0_100",-1)<=100): missing=["type_error:overall"]
        if role=="adversarial" and (obj.get("severity") not in {"none","low","medium","high"} or obj.get("verdict") not in {"pass","fail","uncertain"}): missing=["invalid_adversarial_enum"]
    ans["schema_valid"]=not missing; ans["schema_error"]="missing_keys:"+",".join(missing) if missing else None
    if not ans["schema_valid"]:
        retry=call(base,model,PROMPTS[role]+" Output exactly one JSON object with every required key; no markdown.",user[:8000]); robj=retry.get("json"); rmissing=sorted(SCHEMA[role]-set(robj)) if isinstance(robj,dict) else list(SCHEMA[role]); retry["schema_valid"]=not rmissing; retry["schema_error"]="missing_keys:"+",".join(rmissing) if rmissing else None; ans["retry"]=retry
        if retry["schema_valid"]: return {**retry,"initial_failed":True,"initial_error":ans["schema_error"]}
    return ans

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--max-queries",type=int,default=5); ap.add_argument("--refresh-evidence",action="store_true"); ap.add_argument("--base",default=os.getenv("OLLAMA_HOST","http://127.0.0.1:11434")); a=ap.parse_args()
    cfg=yaml.safe_load(CFG.read_text(encoding="utf-8")); rows=list(csv.DictReader(BANK.open(encoding="utf-8")))[:a.max_queries]; tags=ollama_tags(a.base); models=choose(tags,cfg); results=[]
    for i,row in enumerate(rows,1):
        ev=freeze(row,a.refresh_evidence); d=ask("discovery",a.base,models["discovery"],ev,row["query"]); djson=d.get("json") if d.get("schema_valid") else {}; candidate=djson.get("best_url") if isinstance(djson,dict) else ""
        if candidate and portal_url_allowed(row["portal_id"],candidate) and candidate not in [p["url"] for p in ev["pages"]]:
            s,t,h=get(candidate); ev["pages"].append({"url":candidate,"status":s,"content_type":h.get("content-type",""),"text":re.sub(r"\s+"," ",t)[:25000]}); raw=json.dumps(ev["pages"],ensure_ascii=False,sort_keys=True).encode(); ev["sha256"]=hashlib.sha256(raw).hexdigest()
        prior={"discovery":djson}
        agents={"discovery":d}
        for role in ["semantic","retrieval","metadata","citation"]:
            ans=ask(role,a.base,models[role],ev,row["query"],json.dumps(prior,ensure_ascii=False)); agents[role]=ans; prior[role]=ans.get("json") if ans.get("schema_valid") else {"schema_error":ans.get("schema_error")}
        j=ask("judge",a.base,models["judge"],ev,row["query"],"CANDIDATE OUTPUTS:\n"+json.dumps(prior,ensure_ascii=False)); agents["judge"]=j; jjson=j.get("json") if j.get("schema_valid") else {"schema_error":j.get("schema_error")}
        adv=ask("adversarial",a.base,models["adversarial"],ev,row["query"],"JUDGE RESULT:\n"+json.dumps(jjson,ensure_ascii=False)); agents["adversarial"]=adv
        results.append({"query":row,"repeat":1,"evidence_sha256":ev["sha256"],"candidate_url":candidate,"agents":agents}); print(f"[{i}/{len(rows)}] {row['query_id']} {row['portal_id']} candidate={candidate or 'NONE'}",flush=True)
    OUT.mkdir(parents=True,exist_ok=True); p=OUT/"smoke_retrieval_results.json"; p.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps({"completed":len(results),"models":models,"output":str(p)},ensure_ascii=False,indent=2))

if __name__=="__main__": main()
