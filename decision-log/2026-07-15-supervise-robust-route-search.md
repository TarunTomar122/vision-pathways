# Supervise robust route search completion

## Intended commit subject

`Supervise robust route search completion`

## Problem and decision

The K4/K6/K8 search is resumable at route boundaries and already has two GPU
lanes, but its original shell chains only advance after clean worker exits. A
transient worker crash would leave a lane stalled. Add a bounded supervisor
that verifies process absence before launching a replacement from the existing
checkpoint, then gates finalization, matched-K controls, and analysis on their
actual result artifacts.

## Changed files and behavior

- `scripts/supervise_robust_route_search.py` supervises the fixed lane order
  `generic -> object -> spatial` and `attribute -> counting -> OCR`, without
  launching a second copy of an active family.
- It records its small state under the result root, launches at most twice per
  stopped stage, and exits after analysis is generated.
- `README.md` documents the optional long-run supervisor invocation.
- `scripts/analyze_robust_route_search.py` is included in this commit so the
  supervisor can automatically produce compact matched-K analysis only after
  frozen routes and controls are complete.

## Alternatives considered

- Rely solely on the original shell chains. Rejected because they do not
  restart an unexpectedly failed worker.
- Restart every job unconditionally. Rejected because it could create
  duplicate GPU workers or mask a persistent configuration failure.
- Alter the frozen route-search config or active runner. Rejected because that
  would invalidate the in-flight experiment fingerprint.

## Verification evidence

- `python3 -m py_compile scripts/supervise_robust_route_search.py
  scripts/analyze_robust_route_search.py`
- `PYTHONPATH=src .venv/bin/python scripts/supervise_robust_route_search.py
  --once --dry-run` confirms the current active processes prevent duplicate
  launches.
- The remote process list confirms the two primary workers, both original
  lane chains, finalizer watcher, and control watcher remain active before the
  supervisor is started.

## Limitations and unsupported claims

- The supervisor cannot repair an invalid model, exhausted disk, permanently
  unreachable host, or a deterministic software error; it stops after two
  launch attempts and leaves diagnostics in logs.
- It does not make an accuracy claim and does not access the consumed external
  benchmark.
- It writes compact state but raw prediction caches remain outside Git by
  design.

## Next action enabled

Run the supervisor on the GPU host while the existing experiment is active;
once controls finish it will invoke compact analysis for review and reporting.
