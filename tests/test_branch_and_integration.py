"""Regression coverage for path-sensitive branch deallocation and Sonar report output."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analyzer"))
from mlpca.core import Analyzer, issues_to_sonar


class BranchAndIntegrationTests(unittest.TestCase):
    def analyze(self, code: str):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "sample.c"
            file.write_text(code, encoding="utf-8")
            return Analyzer().analyze_file(str(file))

    def test_each_branch_releases_allocation(self):
        issues = self.analyze("""
            #include <stdlib.h>
            void f(int flag) {
                int *p = malloc(4);
                if (flag) { free(p); }
                else { free(p); }
            }
        """)
        self.assertEqual([], [i.rule for i in issues])

    def test_only_one_branch_releases_allocation(self):
        issues = self.analyze("""
            #include <stdlib.h>
            void f(int flag) {
                int *p = malloc(4);
                if (flag) { free(p); }
            }
        """)
        self.assertIn("ML001", [i.rule for i in issues])

    def test_branch_double_free_detected(self):
        issues = self.analyze("""
            #include <stdlib.h>
            void f(int flag) {
                int *p = malloc(4);
                if (flag) { free(p); free(p); }
                else { free(p); }
            }
        """)
        self.assertIn("ML006", [i.rule for i in issues])

    def test_sonar_output_schema_and_dedup(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "sample.c"
            file.write_text("#include <stdlib.h>\nvoid f(){ int *p=malloc(4); }\n")
            issues = Analyzer().analyze_file(str(file))
            payload = issues_to_sonar(issues + issues, directory)
            self.assertTrue(payload["issues"])
            self.assertEqual(len(issues), len(payload["issues"]))
            item = payload["issues"][0]
            self.assertEqual("mlpca", item["engineId"])
            self.assertEqual("sample.c", item["primaryLocation"]["filePath"])
            self.assertGreaterEqual(item["primaryLocation"]["textRange"]["startLine"], 1)

    def test_cli_complete_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            src = work / "example.c"
            report = work / "issues.json"
            src.write_text("#include <stdlib.h>\nvoid f(){int *p=malloc(8);}\n")
            command = [sys.executable, str(ROOT / "analyzer" / "run.py"), str(src),
                       "--output", str(report)]
            proc = subprocess.run(command, text=True, capture_output=True, cwd=str(ROOT))
            self.assertEqual(0, proc.returncode, proc.stderr)
            payload = json.loads(report.read_text())
            self.assertEqual([], payload["mlpca"]["parseFailures"])
            self.assertEqual(1, payload["mlpca"]["analyzedFiles"])
            self.assertIn("ML001", [x["ruleId"] for x in payload["issues"]])


if __name__ == "__main__":
    unittest.main()
