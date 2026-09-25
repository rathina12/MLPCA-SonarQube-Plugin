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
