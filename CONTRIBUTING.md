# Contributing

Contributions to the MLPCA SonarQube Plugin are welcome.

## Development flow
1. Create a minimal C/C++ fixture that demonstrates the behavior.
2. Run the analyzer against the fixture.
3. Add or update a deterministic regression test.
4. Keep analyzer output stable unless the change intentionally updates the contract.

## Good contributions
Bug fixes, false-positive reductions, new memory-lifecycle rules, alias/path-analysis improvements, performance work, tests, documentation, and SonarQube integration fixes are all useful.

## Pull request checklist
- [ ] A reproducible fixture exists for analyzer behavior changes.
- [ ] Regression tests cover the change.
- [ ] Safe code does not gain a new false positive.
- [ ] Path growth and runtime impact were considered.
- [ ] Rule/documentation changes are described clearly.
