import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analyzer'))
from mlpca.core import Analyzer

class AnalyzerTests(unittest.TestCase):
    def rules(self,name):
        a=Analyzer(); issues=a.analyze_file(str(ROOT/'tests'/'fixtures'/name)); return [i.rule for i in issues]
    def test_simple_leak(self): self.assertIn('ML001', self.rules('simple_leak.c'))
    def test_safe(self): self.assertEqual([], self.rules('safe.c'))
    def test_early_return(self): self.assertIn('ML003', self.rules('early_return.c'))
    def test_alias_free(self): self.assertEqual([], self.rules('alias_safe.c'))
    def test_overwrite(self): self.assertIn('ML002', self.rules('overwrite.c'))
    def test_interproc_free(self): self.assertEqual([], self.rules('interproc_safe.c'))
    def test_double_free(self): self.assertIn('ML006', self.rules('double_free.c'))

if __name__=='__main__': unittest.main()
