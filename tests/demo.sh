#!/bin/sh
# Runs the Phase 3 test suites in order and prints a short summary of each one.
# The browser suites need the Firebase Emulator running with some free memory.
# If a suite cannot open the pages, close the other programs (for example the editor)
# and run that suite alone:
#     python3 -u tests/e2e.py shots
echo "=== 1. Firebase security rules tests (Emulator) ==="
node tests/rules.test.mjs > /tmp/st_rules.log 2>&1
cat /tmp/st_rules.log | grep --line-buffered -E "^FAIL|passed"
echo "=== 2. Phase 2 regression tests (34 cases) ==="
python3 -u tests/e2e.py shots > /tmp/st_e2e.log 2>&1
cat /tmp/st_e2e.log | grep --line-buffered -E "^FAIL|passed"
echo "=== 3. Phase 3 tests ==="
python3 -u tests/p3.py shots > /tmp/st_p3.log 2>&1
cat /tmp/st_p3.log | grep --line-buffered -E "^FAIL|passed"
echo "=== 4. Full journey test (13 steps) ==="
python3 -u tests/full_flow.py shots > /tmp/st_ff.log 2>&1
cat /tmp/st_ff.log | grep --line-buffered -E "^FAIL|passed"
echo "=== All suites finished ==="
