"""Record actual integer resize and padding; map continuous box edges."""
import numpy as np

def transform_record(original_hw, target_hw=(672,672)):
    h,w=map(int,original_hw); th,tw=map(int,target_hw)
    if min(h,w,th,tw)<=0: raise ValueError('Positive dimensions required')
    ratio=min(th/h,tw/w)
    nh,nw=int(ratio*h),int(ratio*w)
    if min(nh,nw)<=0: raise ValueError('Resize collapsed a dimension')
    left,top=(tw-nw)//2,(th-nh)//2
    return {'original_hw':[h,w],'target_hw':[th,tw],'resized_hw':[nh,nw],
            'padding_ltrb':[left,top,tw-nw-left,th-nh-top],
            'scale_xy':[nw/w,nh/h],'ideal_ratio':ratio,
            'coordinate_convention':'continuous box edges; no integer rounding during coordinate mapping'}

def map_boxes(boxes, record, inverse=False, variant='recorded'):
    boxes=np.asarray(boxes,dtype=np.float64).reshape(-1,4)
    sx,sy=record['scale_xy']; left,top,_,_=record['padding_ltrb']
    scale=np.asarray([sx,sy,sx,sy]); pad=np.asarray([left,top,left,top])
    if not inverse:return boxes*scale+pad
    if variant=='missing_padding':pad=np.zeros(4)
    elif variant=='stretch':
        h,w=record['original_hw'];th,tw=record['target_hw']
        scale=np.asarray([tw/w,th/h,tw/w,th/h]);pad=np.zeros(4)
    elif variant=='sdk_ideal':
        h,w=record['original_hw'];th,tw=record['target_hw'];r=record['ideal_ratio']
        scale=np.full(4,r);pad=np.asarray([(tw-r*w)/2,(th-r*h)/2]*2)
    elif variant!='recorded':raise ValueError(variant)
    return (boxes-pad)/scale

def clip_boxes(boxes,original_hw):
    h,w=original_hw
    return np.clip(np.asarray(boxes),[0,0,0,0],[w-1,h-1,w-1,h-1])
