#!/bin/bash
# Runs every StudyMate test suite in order, checks the result of each suite and ends
# with a non-zero exit code when one of them fails.
# The browser suites need the Firebase Emulator running. If a suite cannot open the
# pages, close the other programs and run that suite alone, for example:
#   python3 -u tests/e2e.py shots

mkdir -p shots
FAILED=0
TOTAL=0

check() {
  NAME="$1"; FILE="$2"; EXPECT="$3"
  if [ ! -f "$FILE" ]; then
    echo "FAIL  $NAME: the suite did not write $FILE (it crashed)"
    FAILED=$((FAILED + 1))
    return
  fi
  LINE=$(grep -E "^[0-9]+ / [0-9]+" "$FILE" | tail -1)
  if [ -z "$LINE" ]; then
    echo "FAIL  $NAME: no summary line in $FILE"
    FAILED=$((FAILED + 1))
    return
  fi
  PASS=$(echo "$LINE" | cut -d' ' -f1)
  ALL=$(echo "$LINE" | cut -d' ' -f3)
  TOTAL=$((TOTAL + ALL))
  if [ "$PASS" != "$ALL" ] || [ "$ALL" != "$EXPECT" ]; then
    echo "FAIL  $NAME: $LINE (expected $EXPECT / $EXPECT)"
    FAILED=$((FAILED + 1))
  else
    echo "PASS  $NAME: $LINE"
  fi
}

# Clear the local Firebase Emulator before each test suite.
reset_data() {
  python3 - <<'PY'
import urllib.request

project = "demo-studymate"

urls = [
    f"http://127.0.0.1:8080/emulator/v1/projects/{project}/databases/(default)/documents",
    f"http://127.0.0.1:9099/emulator/v1/projects/{project}/accounts",
]

for url in urls:
    request = urllib.request.Request(url, method="DELETE")
    with urllib.request.urlopen(request, timeout=15) as response:
        print(f"Emulator reset: HTTP {response.status}")
PY
}


echo "=== 1. Phase 1 and 2 regression tests ==="
reset_data || {
  echo "ERROR: Could not reset Firebase Emulator. Check that the emulators are running."
  exit 1
}
python3 -u tests/e2e.py shots > /tmp/st_e2e.log 2>&1
grep -E "^FAIL" /tmp/st_e2e.log
check "Regression" /tmp/st_e2e.log 34

echo "=== 2. Phase 3 tests ==="
reset_data || {
  echo "ERROR: Could not reset Firebase Emulator. Check that the emulators are running."
  exit 1
}
python3 -u tests/p3.py shots > /tmp/st_p3.log 2>&1
grep -E "^FAIL" /tmp/st_p3.log
check "Phase 3" /tmp/st_p3.log 58

echo "=== 3. Full journey test ==="
reset_data || {
  echo "ERROR: Could not reset Firebase Emulator. Check that the emulators are running."
  exit 1
}
python3 -u tests/full_flow.py shots > /tmp/st_ff.log 2>&1
grep -E "^FAIL" /tmp/st_ff.log
check "Full journey" /tmp/st_ff.log 15

echo "=== 4. Firebase security rules tests (Emulator) ==="
reset_data || {
  echo "ERROR: Could not reset Firebase Emulator. Check that the emulators are running."
  exit 1
}
node tests/rules.test.mjs > /tmp/st_rules.log 2>&1
grep -E "^FAIL" /tmp/st_rules.log
check "Security rules" /tmp/st_rules.log 49

echo "=== Result ==="
if [ "$FAILED" -ne 0 ]; then
  echo "FAILED: $FAILED suite(s) did not pass. Nothing is reported as green."
  exit 1
fi
echo "All suites finished: $TOTAL / $TOTAL checks passed"
