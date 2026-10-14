"""Execute the fixed vision CLI and record its actual exit status and artifacts."""
import argparse,json,subprocess,sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['cli','image','model','runner','output','record']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--task',choices=['classify','detect'],required=True)
    p.add_argument('--case',required=True)
    a=p.parse_args()
    if a.output.exists() or a.record.exists():raise FileExistsError('Choose new output and record paths')
    a.record.parent.mkdir(parents=True,exist_ok=True)
    log=a.record.with_suffix('.capture.log')
    if log.exists():raise FileExistsError(log)
    command=[sys.executable,str(a.cli.resolve()),a.task,'--image',str(a.image.resolve()),'--model',str(a.model.resolve()),'--runner',str(a.runner.resolve()),'--output',str(a.output.resolve())]
    with log.open('w') as f:process=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
    output=a.output.resolve();normalized=a.record.with_suffix('.normalized.json')
    if normalized.exists():raise FileExistsError(normalized)
    if process.returncode==0:
        result=json.loads((output/'result.json').read_text())
        if a.task=='classify':result={'top5_ids':[r['class_id'] for r in result['top5']]}
        else:result={'boxes':[[*r['xyxy'],r['score'],r['class_id']] for r in result['detections']]}
        normalized.write_text(json.dumps(result,indent=2))
    if a.task=='classify':inputs={'input':output/'input_int8.bin'};outputs={'output':output/'ucp/output_int32.bin'}
    else:inputs={'y':output/'input_y.bin','uv':output/'input_uv.bin'};outputs={str(i):output/'ucp'/f'output_{i}.bin' for i in range(3)}
    run={'run_id':a.case,'baseline_case':a.case,'group':'fresh_cli','origin':'fresh process executed by capture_cli_record.py',
         'exit_code':process.returncode,'command':command,'model':str(a.model.resolve()),
         'inputs':{k:str(v) for k,v in inputs.items()},'outputs':{k:str(v) for k,v in outputs.items()},'result':str(normalized.resolve())}
    a.record.write_text(json.dumps([run],indent=2))
    print(f'exit={process.returncode} record={a.record}')
    return process.returncode
if __name__=='__main__':raise SystemExit(main())
