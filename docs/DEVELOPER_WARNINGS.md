# Developer Warnings

These are the guardrails we want every future teammate to read before modifying the project.

## Environment And Git Isolation

- Do not experiment directly in the only working environment.
- Before risky dependency changes, create a backup or a fresh environment first.
- Commit or tag a known-good state before touching dependency pins, Python environments, or hardware access code.
- Keep source code, caches, outputs, and local environment directories isolated from each other.
- Do not upload `.conda-env`, `.pip-cache`, `.localhome`, `outputs/`, or local model caches to GitHub.

## Hugging Face And Large Artifacts

- Datasets and trained policies belong on Hugging Face, not in Git history.
- Keep README links pointing to the public dataset and public model rather than checking those blobs into the repo.
- When inference uses a local mirror of a Hugging Face model, treat it as a cache, not as source code.

## Backend Startup

- Start the backend from the Python environment that already contains `lerobot`.
- Always provide `PYTHONPATH` to the matching LeRobot source tree.
- If the backend can start but subprocesses cannot import `lerobot`, assume the startup command is wrong before changing code.

## Camera And Hardware Access

- On macOS, camera permission is granted to the app process chain, not only to the Python binary.
- If cameras suddenly disappear, verify TCC authorization before debugging OpenCV indexes.
- Never assume a serial port is free just because the previous UI action looks finished. Check whether the process actually exited.

## Bimanual Configuration

- Left and right arm IDs must remain consistent with the base-ID convention used by LeRobot.
- Calibration files for bimanual sub-arms must still live under `so101_follower` and `so101_leader`.
- A naming mismatch in calibration IDs looks like a motor or teleoperation failure even when the real problem is file lookup.

## Evaluation Runs

- Evaluation dataset names should start with `eval_`.
- Reuse of old evaluation names can collide with local Hugging Face cache directories.
- If an evaluation run fails before motion starts, check cache collisions and repo naming before investigating the policy.

## License Boundary

- This repository is MIT.
- The linked LeRobot fork and any upstream-derived code keep their own original license terms.
- Do not relabel third-party derived code as MIT just because the UI repo is MIT.
