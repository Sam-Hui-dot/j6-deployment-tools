"""Map box coordinates using the transform saved by preprocessing."""
import argparse,json
from pathlib import Path
from geometry_transform import map_boxes,clip_boxes
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--record',type=Path,required=True);p.add_argument('--boxes',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
p.add_argument('--forward',action='store_true');p.add_argument('--clip',action='store_true');args=p.parse_args()
if args.output.exists():raise FileExistsError('Choose a new output file')
record=json.loads(args.record.read_text(encoding='utf-8'));record=record.get('transform',record)
boxes=json.loads(args.boxes.read_text(encoding='utf-8'))
result=map_boxes(boxes,record,inverse=not args.forward)
if args.clip:
    if args.forward:raise ValueError('--clip applies only to inverse mapping')
    result=clip_boxes(result,record['original_hw'])
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result.tolist(),indent=2),encoding='utf-8')
print(f'{len(result)} boxes -> {args.output}')
