# Architecture

## Pipeline
1. Compilation context — read `compile_commands.json` when present.
2. Clang frontend — syntax-check and emit semantic AST JSON.
3. Program model — identify functions, variables, calls, aliases and allocation events.
4. Partial call-path engine — fork on branches, abstract loops as zero/representative iteration, merge equivalent states, and enforce a configurable path budget.
5. Memory state machine — track each allocation object independently from pointer variable names.
6. Interprocedural summaries — recognize user functions that release pointer parameters.
7. Issue engine — deduplicate and emit rule-coded findings.
8. Sonar adapter — serialize JSON and import it through a scanner Sensor.

## Allocation state model
`ALLOCATED -> FREED | ESCAPED | LEAKED`

Variables are aliases of allocation objects. Freeing through any alias frees the allocation object; overwriting one alias only causes a leak when no remaining alias reaches the old allocation.

## Path explosion control
Every state has a canonical signature based on termination flag, variable-to-allocation mapping, allocation states, and aliases. Equivalent states are merged. `max_paths_per_function` provides a hard safety bound. Loops use a zero-iteration path and one representative body iteration in v1.0.0.

## Sonar separation
The analyzer is intentionally independent of SonarQube. It writes `.mlpca/issues.json`; the Java plugin imports that file.
