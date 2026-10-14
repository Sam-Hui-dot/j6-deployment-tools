"""Compare fixed-model deployment artifacts; standard-library-only, no inference."""
import argparse
import hashlib
import json
import math
from pathlib import Path

def file_signature(path):
    with path.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
    return {'bytes':path.stat().st_size,'sha256':digest}

def semantic_equal(a,b,tolerance):
    if isinstance(a,bool) or isinstance(b,bool):return type(a)==type(b) and a==b
    if isinstance(a,int) and isinstance(b,int):return a==b
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):
        return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tolerance
    if isinstance(a,list) and isinstance(b,list):
        return len(a)==len(b) and all(semantic_equal(x,y,tolerance) for x,y in zip(a,b))
    if isinstance(a,dict) and isinstance(b,dict):
        return a.keys()==b.keys() and all(semantic_equal(a[k],b[k],tolerance) for k in a)
    return type(a)==type(b) and a==b

def task_equal(expected,actual,tolerance):
    if isinstance(expected,dict) and isinstance(actual,dict) and expected.keys()==actual.keys()=={'boxes'}:
        reference,prediction=expected['boxes'],actual['boxes']
        if not isinstance(reference,list) or not isinstance(prediction,list) or len(reference)!=len(prediction):return False
        for box in reference+prediction:
            if not isinstance(box,list) or len(box)!=6:return False
            if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in box):return False
            if box[5]!=int(box[5]):return False
        # An unordered multiset comparison, including duplicate boxes. Augmenting paths
        # avoid the false negatives a greedy first-match rule can cause.
        edges=[[j for j,b in enumerate(prediction) if a[5]==b[5] and semantic_equal(a[:5],b[:5],tolerance)] for a in reference]
        matched={}
        def augment(i,seen):
            for j in edges[i]:
                if j in seen:continue
                seen.add(j)
                if j not in matched or augment(matched[j],seen):matched[j]=i;return True
            return False
        return all(augment(i,set()) for i in range(len(reference)))
    return semantic_equal(expected,actual,tolerance)

def verify(expected,run,base_dir,tolerance=1e-5):
    checks={k:[] for k in ['model','structure','execution','input','raw','result']}
    if not isinstance(run.get('exit_code'),int) or isinstance(run.get('exit_code'),bool) or run['exit_code']!=0:
        checks['execution'].append('Nonzero or missing recorded process exit code')
    try:
        if file_signature(base_dir/run['model'])['sha256']!=expected['model_sha256']:
            checks['model'].append('Model hash differs; inspect and explicitly re-baseline if intended')
    except (OSError,KeyError,TypeError) as e:checks['model'].append(str(e))
    for field,phase in [('inputs','input'),('outputs','raw')]:
        supplied=run.get(field,{})
        if not isinstance(supplied,dict):
            checks['structure'].append(f'{field}: expected named file map');continue
        if set(supplied)!=set(expected[field]):checks['structure'].append(f'{field}: file names differ')
        for name,wanted in expected[field].items():
            try:actual=file_signature(base_dir/supplied[name])
            except (OSError,KeyError,TypeError) as e:
                checks['structure'].append(f'{field}/{name}: {e}');continue
            if actual['bytes']!=wanted['bytes']:checks['structure'].append(f'{field}/{name}: byte length differs')
            if actual['sha256']!=wanted['sha256']:checks[phase].append(f'{field}/{name}: bytes differ from trusted baseline')
    try:
        result=json.loads((base_dir/run['result']).read_text(encoding='utf-8'))
        if not task_equal(expected['result'],result,tolerance):checks['result'].append('Normalized task result differs')
    except (OSError,KeyError,TypeError,ValueError) as e:checks['result'].append(str(e))
    return {'passed':not any(checks.values()),'checks':{k:{'passed':not errors,'errors':errors} for k,errors in checks.items()}}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--runs',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--tolerance',type=float,default=1e-5)
    args=p.parse_args()
    if not math.isfinite(args.tolerance) or args.tolerance<0:p.error('Tolerance must be finite and nonnegative')
    if args.report.exists():raise FileExistsError('Preserve existing report; choose a new output')
    baseline=json.loads(args.baseline.read_text(encoding='utf-8'))
    runs=json.loads(args.runs.read_text(encoding='utf-8'))
    if not isinstance(runs,list) or not runs:raise ValueError('At least one run is required')
    if len({r['run_id'] for r in runs})!=len(runs):raise ValueError('Duplicate run identifiers')
    rows=[]
    for run in runs:
        if run['baseline_case'] not in baseline['cases']:raise ValueError('Unknown baseline case')
        value=verify(baseline['cases'][run['baseline_case']],run,args.runs.parent,args.tolerance)
        rows.append({'run_id':run['run_id'],'baseline_case':run['baseline_case'],
                     'group':run.get('group','unspecified'),'origin':run.get('origin','user supplied'),**value})
    report={'scope':'artifact regression against trusted fixed model/input/output/task baselines; not task accuracy or inferred process status',
            'runs':len(rows),'passed':sum(v['passed'] for v in rows),'rows':rows}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"{report['passed']}/{report['runs']} passed; report={args.report}")
    return 0 if report['passed']==report['runs'] else 1

if __name__=='__main__':raise SystemExit(main())
