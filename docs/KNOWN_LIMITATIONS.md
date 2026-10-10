# Known limitations and safe handling

No static analyzer can guarantee zero false positives/negatives for unrestricted C/C++. MLPCA v1 deliberately scopes hard cases rather than pretending they are solved.

- Function pointers / virtual dispatch: unresolved targets are not assumed to free memory.
- Cross-thread ownership: treat transfer APIs as configured ownership sinks.
- Memory pools / arenas: configure pool ownership/release APIs.
- Exceptions: v1 is focused on explicit control flow.
- Smart pointers: v1 focuses on raw ownership.
- Macro locations: unusual expansions can map findings to the expansion line.
- Compiler-specific syntax: Clang parse failures are reported, never silently treated as clean.
- Path cap: branch-heavy functions may be truncated to the configured path budget.

## Ownership-analysis caveats

- `realloc` and `reallocarray` have success and failure outcomes. Direct assignment to an owned pointer is flagged as an ML008 risk; this bounded model does not prove both outcomes or the correctness of every conditional recovery path.
- An unknown function call may free, retain, or transfer ownership; explicit summaries and configured sinks are only approximations.
- Assignment tracking handles straightforward pointer variables, not all lvalues (struct fields, pointer indirection, array entries, overloaded operators).
- Conditional expressions, early exits, switch statements, nested calls, exception edges and loop paths are not exhaustively modeled. A clean report is not proof that a program has no memory leaks.
- SonarQube integration imports an existing report and does not execute the analyzer itself. Validate the analyzer CLI and scanner independently on the target SonarQube version.
