import json, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analyzer'))
from mlpca.core import Analyzer
from mlpca.cli import compile_db_args

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
    def test_realloc_direct_assignment(self):
        rules = self.rules('realloc_direct_assign.c')
        self.assertIn('ML008', rules)
        self.assertNotIn('ML002', rules)

    def test_reassign_null_reports_overwrite(self):
        self.assertIn('ML002', self.rules('reassign_null_leak.c'))

    def test_alias_survives_reassignment(self):
        self.assertEqual([], self.rules('reassign_alias_safe.c'))

    def test_self_assignment_does_not_lose_ownership(self):
        self.assertEqual([], self.rules('self_assignment_safe.c'))

    def test_compile_database_relative_source_and_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / 'src').mkdir()
            src = project / 'src' / 'sample.c'
            src.write_text('int main(void) { return 0; }')
            commands = [{
                'directory': str(project),
                'file': 'src/sample.c',
                'arguments': ['clang', '-c', 'src/sample.c', '-std=c99',
                              '-Iinclude', '-o', 'sample.o', '-DTEST=1']
            }]
            (project / 'compile_commands.json').write_text(json.dumps(commands))
            args = compile_db_args(project)[str(src.resolve())]
            self.assertIn('-DTEST=1', args)
            self.assertIn('-Iinclude', args)
            self.assertNotIn('-c', args)
            self.assertNotIn('-std=c99', args)
            self.assertNotIn('-o', args)
            self.assertNotIn('sample.o', args)

if __name__=='__main__': unittest.main()
