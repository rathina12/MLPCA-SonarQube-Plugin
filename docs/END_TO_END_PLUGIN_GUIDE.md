# MLPCA — From C/C++ source to SonarQube (PoC to plugin)

## Prerequisites

- Python 3.10+; Clang 15+ installed and available on `PATH`
- Java 17+, Maven 3.9+ to package the Java SonarQube plugin
- A supported, self-managed SonarQube Server and SonarScanner for **live** integration tests
- Analyzer and scanner must use the **same project root** for source-file mapping

## 1. Verify analyzer and regression suite

From repository root:

```bash
python -m unittest discover -s tests -v
python -m compileall -q analyzer
python analyzer/run.py examples --output .mlpca/issues.json
```

Inspect `.mlpca/issues.json`. The analyzer should produce an `issues` array with `engineId`, `ruleId`, severity, file path, line number and message. The `mlpca` section includes parse failures.

If Clang parsing fails, the CLI returns nonzero and the failure is recorded; parse failure **never** means the source is clean.

### Additional safety

```bash
python analyzer/run.py examples --fail-on-issues
```

This returns a nonzero exit code when confirmed issues are found (or on parse failures).

## 2. Package the plugin

```bash
mvn -B -f sonar-plugin/pom.xml clean package
```

Look for the generated plugin jar under `sonar-plugin/target/`. The GitHub CI builds the plugin on Java 17; a successful build **does not prove** deployment and live issue import.

## 3. Install to a SonarQube Server

1. Verify your installed SonarQube Server's Java/plugin API compatibility.
2. Stop the self-managed SonarQube Server.
3. Copy the built plugin JAR into the server's `extensions/plugins/` directory.
4. Start SonarQube and inspect its startup logs for successful plugin loading.
5. Use `sonar-project.properties.example` as a starting point for `sonar-project.properties`.
6. Run the Python analyzer *before* SonarScanner from the project root.
7. Run SonarScanner with your SonarQube project key and authentication token.
8. Open the SonarQube project's external issues and confirm source locations and rules.

**Never commit SonarQube authentication tokens or other secrets.**

For SonarCloud or managed SonarQube services that do not allow user-installed plugins, use a supported generic external-issues import mechanism instead of assuming custom plugin deployment.

## 4. What the integration does

```text
C/C++ source
  -> Clang AST JSON
  -> Python MLPCA path/lifecycle analysis
  -> .mlpca/issues.json
  -> Java SonarQube sensor
  -> External issues shown in SonarQube
```

The sensor reads `sonar.mlpca.reportPath` (default `.mlpca/issues.json`), rejects malformed reports that lack an issues array, normalizes relative file paths and imports matching indexed source file locations.

## 5. Verification matrix

| Scope | Evidence |
|---|---|
| Analyzer unit regressions | `python -m unittest discover -s tests -v` |
| Python syntax check | `python -m compileall -q analyzer` |
| CLI-to-JSON smoke | `python analyzer/run.py examples --output .mlpca/issues.json` |
| Java plugin compile/package | `mvn -f sonar-plugin/pom.xml clean package` and CI plugin job |
| Live plugin loading | **Not verified without a SonarQube server** |
| Live SonarScanner issue import | **Not verified without scanner/server** |
| Large project accuracy | Not established by unit tests; measure with labeled benchmarks |

## 6. Current implementation limits

This is a proof of concept, not a proof that every C/C++ path is understood. Unresolved call targets, thread ownership, complex RAII, exception flows, macro mapping, path-cap truncation and some cross-TU ownership require stronger analysis. Path merging is based on state signatures and bounded path budgets. There is no measured precision/recall guarantee from the current tests.
