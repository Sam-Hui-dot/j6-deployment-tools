import copy,json,tempfile,unittest
from pathlib import Path
from regression_check import verify,file_signature,semantic_equal,task_equal

class RegressionChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        for name,data in [('model',b'model'),('input',b'input'),('output',b'output')]: (self.root/name).write_bytes(data)
        (self.root/'result.json').write_text('{"values": [[1.0, 2.0]]}')
        self.expected={'model_sha256':file_signature(self.root/'model')['sha256'],
            'inputs':{'input':file_signature(self.root/'input')},'outputs':{'output':file_signature(self.root/'output')},
            'result':{'values':[[1.0,2.0]]}}
        self.run={'exit_code':0,'model':'model','inputs':{'input':'input'},'outputs':{'output':'output'},'result':'result.json'}
    def tearDown(self):self.tmp.cleanup()
    def test_control(self):self.assertTrue(verify(self.expected,self.run,self.root)['passed'])
    def test_same_size_input_change(self):
        (self.root/'input').write_bytes(b'INPUT');c=verify(self.expected,self.run,self.root)['checks']
        self.assertTrue(c['structure']['passed']);self.assertFalse(c['input']['passed'])
    def test_raw_change_with_same_result(self):
        (self.root/'output').write_bytes(b'OUTPUT');c=verify(self.expected,self.run,self.root)['checks']
        self.assertTrue(c['result']['passed']);self.assertFalse(c['raw']['passed'])
    def test_result_change_with_same_raw(self):
        (self.root/'result.json').write_text('{"values": [[10.0, 2.0]]}');c=verify(self.expected,self.run,self.root)['checks']
        self.assertTrue(c['raw']['passed']);self.assertFalse(c['result']['passed'])
    def test_missing_file(self):
        (self.root/'output').unlink();self.assertFalse(verify(self.expected,self.run,self.root)['checks']['structure']['passed'])
    def test_truncation(self):
        (self.root/'output').write_bytes(b'o');self.assertFalse(verify(self.expected,self.run,self.root)['checks']['structure']['passed'])
    def test_changed_model(self):
        (self.root/'model').write_bytes(b'changed');self.assertFalse(verify(self.expected,self.run,self.root)['checks']['model']['passed'])
    def test_failed_exit_even_with_stale_good_outputs(self):
        self.run['exit_code']=1;self.assertFalse(verify(self.expected,self.run,self.root)['checks']['execution']['passed'])
    def test_missing_exit_does_not_mean_zero(self):
        del self.run['exit_code'];self.assertFalse(verify(self.expected,self.run,self.root)['checks']['execution']['passed'])
    def test_nan_result_rejected(self):
        self.assertFalse(semantic_equal(float('nan'),float('nan'),1e-5))
    def test_tolerance_and_exact_class_ids(self):
        self.assertTrue(semantic_equal([1.0],[1.000001],1e-5));self.assertFalse(semantic_equal([1],[2],100))
    def test_common_wrong_baseline_is_not_discovered(self):
        # A checker cannot validate the scientific correctness of its trusted baseline.
        (self.root/'input').write_bytes(b'wrong');wrong=copy.deepcopy(self.expected)
        wrong['inputs']['input']=file_signature(self.root/'input')
        self.assertTrue(verify(wrong,self.run,self.root)['passed'])
    def test_detection_order_does_not_change_result(self):
        a={'boxes':[[1.,2.,3.,4.,.5,0],[6.,7.,8.,9.,.8,1]]}
        self.assertTrue(task_equal(a,{'boxes':list(reversed(a['boxes']))},1e-5))
    def test_top5_order_is_meaningful(self):
        self.assertFalse(task_equal({'top5_ids':[1,2]},{'top5_ids':[2,1]},1e-5))
    def test_duplicate_boxes_cannot_reuse_one_match(self):
        a=[1.,2.,3.,4.,.5,0];b=[6.,7.,8.,9.,.8,1]
        self.assertFalse(task_equal({'boxes':[a,b]},{'boxes':[a,a]},1e-5))
    def test_augmenting_path_in_ambiguous_tolerance_region(self):
        def b(x):return [float(x),0.,2.,2.,.5,0]
        self.assertTrue(task_equal({'boxes':[b(.5),b(0)]},{'boxes':[b(0),b(1)]},.51))

if __name__=='__main__':unittest.main()
