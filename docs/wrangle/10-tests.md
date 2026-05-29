# Tests & verification

> **Read.** No automated tests exist. Verification is entirely manual — send a command to the bot in Webex and read the response.

## What's actually here

No test files, no test framework, no test runner. `tests/` directory was created by the claude-kit init scaffold (`tests/suites/`, `tests/stamps/`, etc.) but contains no project tests.

`test_sql.py` exists at the repo root — it appears to be a one-off manual SQL connection script used during development, not a test suite.

No `pytest`, `unittest`, or similar in `requirements.txt`. No CI configuration (no `.github/`, no `Makefile` with a `test` target).

## How it fits

There is no automated verification gate before deploy. All commands are verified by manually sending them in a Webex space.

## Open questions

- Does `test_sql.py` do anything meaningful? (Not read during this audit — it's a dev scratch file.)
- Is there a desire for integration tests against a CUCM sandbox or mock?
