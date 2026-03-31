# Bug Log

This log tracks the main bugs and failure modes we found while building and demoing the project.

| ID | Status | Summary | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| BUG-001 | Open environment issue | macOS camera permission may stay blocked for the `Codex.app -> python` process chain even after a user clicks allow once. | Camera detection and preview fail before inference or recording can proceed. | Re-check TCC state, relaunch the host app, and re-test camera access from the same Python executable. |
| BUG-002 | Fixed in UI backend | Re-running inference with the same evaluation dataset name can fail with a local Hugging Face cache `FileExistsError`. | Inference aborts before the next evaluation run starts. | The backend now clears stale local eval cache for the requested `repo_id` before launch. Use unique evaluation names anyway. |
| BUG-003 | Fixed in startup flow | Backend and inference subprocesses can fail with `ModuleNotFoundError: No module named 'lerobot'` when `PYTHONPATH` does not include the local LeRobot source tree. | Backend starts, but subprocess commands fail at runtime. | Always start the backend with `PYTHONPATH=/path/to/lerobot-MakerMods/src`. |
| BUG-004 | Fixed | Bimanual calibration paths were mismatched with the sub-arm type directories used by LeRobot. | Teleoperation failed because the subprocess could not locate the expected calibration files. | Calibration paths now target `so101_follower` and `so101_leader` for the actual sub-arm instances. |
| BUG-005 | Fixed | Serial port locks could remain held after subprocess crashes or abnormal termination. | Later teleoperation, recording, or inference attempts reported the port as busy. | Port lock cleanup now runs when the process exits, not only when the stop endpoint is clicked. |
| BUG-006 | Fixed | Switching tabs while camera streams or teleoperation were active could block the event loop and hang the backend. | UI became unresponsive and camera workers did not stop cleanly. | Camera operations were moved off the event loop and stream shutdown logic was made non-blocking. |
| BUG-007 | Fixed | Inference startup felt like a crash because the policy was loaded before robot connection and the UI gave little feedback. | Operators assumed inference had frozen. | The UI now explains auto-stop timing and the backend prefers the local cached model directory when available. |

## Reproduction Notes

### BUG-001

- Symptom: camera enumeration returns authorization errors or empty camera lists.
- Typical hint: OpenCV reports that capture is not authorized.
- Most likely root cause: macOS TCC permission did not fully propagate to the current app session.

### BUG-002

- Symptom: same evaluation dataset name used twice.
- Typical error: `FileExistsError` under `~/.cache/huggingface/lerobot/...`.
- Root cause: LeRobot expects a fresh local dataset directory for each evaluation write.

### BUG-003

- Symptom: subprocess launch succeeds but import fails immediately.
- Typical error: `ModuleNotFoundError` or failure resolving `lerobot.scripts.*`.
- Root cause: backend Python executable was correct, but source path injection was missing.

## Recommended Triage Order

1. Confirm camera permission state.
2. Confirm `PYTHONPATH`.
3. Confirm calibration IDs and left/right pairing.
4. Confirm serial ports are not still locked.
5. Confirm evaluation dataset name is unique.
