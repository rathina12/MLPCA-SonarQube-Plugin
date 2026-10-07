# Validation plan

Regression cases:
- definite leak at normal exit
- safe allocate/free
- leak on early return
- alias freed through another pointer
- pointer overwrite
- user function freeing an argument
- double free

Research metrics:
- files/functions analyzed
- execution states explored before/after merging
- analysis wall time
- peak RSS
- true positives / false positives / false negatives
- parse failures

## Automated checks and release gate

Run `bash scripts/test.sh` and `mvn -B -f sonar-plugin/pom.xml clean package`.
GitHub Actions runs both jobs on each push and pull request.

A successful CI run checks the existing regression suite, Python syntax, an
end-to-end JSON report, and Maven packaging. It does **not** prove correct
SonarQube runtime import, zero false positives or false negatives, or complete
control-flow coverage. A release additionally needs:
- Real scanner + SonarQube integration tests across supported versions.
- C and C++ fixture matrices for branches, nested calls, switches and loops.
- Held-out Juliet CWE-401 benchmark with confusion matrix and timing.
- Verification of external issue line numbers, severity and path mapping.
- Security and dependency review; repeatable environment/version matrix.

The analyzer currently implements ML001, ML002, ML003, ML006, ML007 and ML008.
ML004/ML005 are reserved identifiers, not implemented detectors. Unused
`loop_unroll` configuration has been removed; loops currently use the fixed
skip/representative-iteration abstraction.
