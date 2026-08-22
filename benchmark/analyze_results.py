"""Analyze completed local benchmark results and association with AEO score."""
from __future__ import annotations
import csv, itertools, math
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/"benchmark/results/results.csv"
MATRIX=ROOT/"execution/expanded-audit-matrix-2026-08-22.csv"
OUT=ROOT/"benchmark/results"

def mean(xs): return sum(xs)/len(xs) if xs else float('nan')

def rank(xs):
    order=sorted(enumerate(xs), key=lambda z:z[1]); out=[0.0]*len(xs); i=0
    while i<len(order):
        j=i
        while j+1<len(order) and order[j+1][1]==order[i][1]: j+=1
        r=(i+j+2)/2
        for k in range(i,j+1): out[order[k][0]]=r
        i=j+1
    return out

def spearman(x,y):
    if len(x)<2: return float('nan')
    rx,ry=rank(x),rank(y); mx,my=mean(rx),mean(ry)
    den=math.sqrt(sum((a-mx)**2 for a in rx)*sum((b-my)**2 for b in ry))
    return sum((a-mx)*(b-my) for a,b in zip(rx,ry))/den if den else float('nan')

def exact_perm_p(x,y,observed):
    # two-sided exact permutation test on rank correlation for small portal-level n
    count=0; total=0
    for perm in itertools.permutations(y):
        rho=spearman(x,list(perm)); total+=1
        if abs(rho) >= abs(observed)-1e-12: count+=1
    return count/total if total else float('nan')

def load_results():
    with RESULTS.open(encoding='utf-8') as f: return list(csv.DictReader(f))

def load_matrix():
    with MATRIX.open(encoding='utf-8') as f: return list(csv.DictReader(f))

def main():
    rows=load_results(); mat=load_matrix(); score={r['portal_id']:float(r['score']) for r in mat}
    grouped=defaultdict(list)
    for r in rows:
        try:
            v=float(r['overall_0_100'])
        except (TypeError,ValueError): continue
        grouped[r['portal_id']].append(v)
    summary=[]
    for p,vals in grouped.items(): summary.append({'portal_id':p,'n_runs':len(vals),'mean_airsc':mean(vals),'median_airsc':sorted(vals)[len(vals)//2]})
    common=[r for r in summary if r['portal_id'] in score]
    x=[score[r['portal_id']] for r in common]; y=[r['mean_airsc'] for r in common]
    rho=spearman(x,y); p=exact_perm_p(x,y,rho) if len(common)<=8 else float('nan')
    out={'n_rows':len(rows),'portal_summary':summary,'portal_level_spearman':rho,'exact_permutation_p':p,'warning':'Results are repeated measures clustered by query; portal-level n is the number of portals, not execution count.'}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'analysis_summary.json').write_text(__import__('json').dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    with (OUT/'portal_summary.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=summary[0].keys() if summary else ['portal_id','n_runs','mean_airsc','median_airsc']); w.writeheader(); w.writerows(summary)
    print(__import__('json').dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
