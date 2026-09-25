# MLPCA — Memory Leak Detection for SonarQube

MLPCA is a path-sensitive C/C++ static analyzer plus a SonarQube scanner plugin. The analyzer uses Clang's semantic AST JSON, tracks allocation ownership across representative execution paths, merges equivalent states to control path explosion, and emits Sonar-compatible findings.

## What is implemented
- Clang-backed parsing for C and C++17.
- Path-sensitive `if` exploration and bounded representative loop exploration.
- State merging / path cap to avoid exponential blow-up.
- Allocation-object tracking with pointer aliases.
- malloc/calloc/aligned_alloc/valloc, free, realloc family handling.
- C++ new/delete mismatch handling.
- Early-return leak detection.
- Pointer-overwrite leak detection.
- Double-free/double-delete detection.
- Basic interprocedural summaries.
- Ownership escape configuration.
- compile_commands.json support.
- Sonar external issue JSON output.
- Java SonarQube plugin source.
- Regression tests.

## Requirements
- Python 3.10+
- Clang 15+
- Java 17+
- Maven 3.9+

## Run
```bash
python analyzer/run.py . --output .mlpca/issues.json
```

## Build plugin
```bash
cd sonar-plugin
mvn clean package
```

See `docs/` for architecture, limitations, and validation.
