# MakerMods LeRobot UI

Hackathon delivery repository for our MakerMods + LeRobot workflow. This repo packages the Web UI, the public Hugging Face artifacts, the delivery video, and the engineering notes we want reviewers and future developers to see first.

## Deliverables

- **Web UI source code**: this repository
- **LeRobot fork used by the project**: [Maker-Mods/lerobot-MakerMods](https://github.com/Maker-Mods/lerobot-MakerMods)
- **Hugging Face dataset**: [Adkid/pickupbreadCombine12](https://huggingface.co/datasets/Adkid/pickupbreadCombine12)
- **Qualia-trained model**: [qualia-robotics/act-pickupbreadcombine12-e0ad61c9](https://huggingface.co/qualia-robotics/act-pickupbreadcombine12-e0ad61c9)
- **Delivery video**: [docs/assets/makermods-delivery-video.mp4](docs/assets/makermods-delivery-video.mp4)
- **Bug log**: [docs/BUG_LOG.md](docs/BUG_LOG.md)
- **Developer warnings**: [docs/DEVELOPER_WARNINGS.md](docs/DEVELOPER_WARNINGS.md)

## Demo Video

[![MakerMods delivery video preview](docs/assets/makermods-delivery-poster.png)](docs/assets/makermods-delivery-video.mp4)

GitHub does not reliably inline-play repository MP4 files inside `README.md`. The preview image above is clickable and opens the full video in the repo.

## Project Overview

This UI wraps the LeRobot CLI into a browser-based workflow for:

- robot setup
- serial port assignment
- camera detection and preview
- calibration
- teleoperation
- dataset recording
- Qualia training job submission
- policy inference

The backend runs FastAPI and shells out to LeRobot commands. The frontend is a Next.js wizard intended to reduce operator error during demos and data collection.

## Actual Project Status

This repository reflects the real hackathon delivery state rather than an idealized product state.

- The Web UI, backend APIs, and hardware workflow were all implemented and used together.
- Auto calibration works through the UI.
- Teleoperation issues were debugged and fixed in the current codebase.
- The dataset and Qualia-trained model were successfully produced and published to Hugging Face.
- The final delivery video is included in this repository as a reproducible project artifact.
- The system still has environment-sensitive and machine-specific caveats, especially around macOS camera permissions, local Python path setup, and hardware port stability.

In other words: this is a working hackathon software delivery with real engineering progress, but it still needs hardening before being treated as a polished production robotics stack.

## Artifact Links

| Artifact | Link | Notes |
| --- | --- | --- |
| Dataset | [Adkid/pickupbreadCombine12](https://huggingface.co/datasets/Adkid/pickupbreadCombine12) | Main LeRobot dataset used for training |
| Model | [qualia-robotics/act-pickupbreadcombine12-e0ad61c9](https://huggingface.co/qualia-robotics/act-pickupbreadcombine12-e0ad61c9) | ACT model trained through Qualia |
| LeRobot fork | [Maker-Mods/lerobot-MakerMods](https://github.com/Maker-Mods/lerobot-MakerMods) | Robot-side and LeRobot-side changes |
| Delivery video | [docs/assets/makermods-delivery-video.mp4](docs/assets/makermods-delivery-video.mp4) | Final project demo video |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- a working LeRobot environment
- access to the companion fork: [Maker-Mods/lerobot-MakerMods](https://github.com/Maker-Mods/lerobot-MakerMods)

### Backend

Use the same Python environment that contains `lerobot`.

```bash
cd /path/to/MakerMods-LeRobot-UI
PYTHONPATH=/path/to/lerobot-MakerMods/src python -m backend.main
```

### Frontend

```bash
cd /path/to/MakerMods-LeRobot-UI/frontend
npm install
npm run dev
```

Then open `http://localhost:3000`.

## Deployment Recommendations

For future demos or team handoff, we recommend deploying the system with clear separation between source code, runtime environment, and model/data artifacts.

### Recommended deployment shape

1. Keep this repository as the application layer:
   - frontend
   - backend
   - scripts
   - docs
2. Keep the LeRobot fork in a separate repository checkout.
3. Keep Python environments outside the Git working tree when possible.
4. Keep datasets and trained models on Hugging Face instead of storing them in Git.

### Recommended runtime setup

- Prefer a dedicated Linux or Jetson runtime for stable hardware demos.
- If macOS must be used, verify camera and serial permissions before the demo day.
- Start the backend with an explicit `PYTHONPATH` to the LeRobot source tree.
- Run the frontend and backend as separate processes so logs and failures are easier to isolate.
- Keep a known-good fallback model cached locally before live demos.

### Practical deployment advice

- Tag a known-good commit before changing hardware, dependencies, or calibration logic.
- Keep one stable environment for demos and a second isolated environment for experiments.
- Back up calibration files and working config before re-calibration.
- Treat local caches as disposable; treat datasets and models on Hugging Face as the source of truth.

## Environment Incident And Isolation Note

Our first local environment setup did not stay healthy. We kept the failed state for reference under the local LeRobot workspace as:

- `.conda-env-broken-20260329-142732`
- `.sparse-backup-20260329`

That failure is exactly why this project now treats environment state, source code, caches, and public artifacts as separate concerns. The practical rule is simple:

1. commit or tag a known-good state before large dependency or hardware changes
2. use a separate environment for risky experiments
3. keep local caches and generated outputs out of Git
4. push large datasets and models to Hugging Face instead of GitHub

Additional notes are in [docs/DEVELOPER_WARNINGS.md](docs/DEVELOPER_WARNINGS.md).

## Known Issues And Developer Notes

- Bug tracking and reproduction notes: [docs/BUG_LOG.md](docs/BUG_LOG.md)
- Developer warnings and setup caveats: [docs/DEVELOPER_WARNINGS.md](docs/DEVELOPER_WARNINGS.md)

The most important recurring pitfalls were:

- macOS camera permission must be granted to the host app process, not only to Python
- inference must start with a valid `PYTHONPATH` pointing to the LeRobot source tree
- evaluation dataset names should be unique and should start with `eval_`
- serial ports and calibration files need strict left/right ID consistency in bimanual mode

## Future Improvements

The next iteration should focus less on adding features and more on reducing operational fragility.

- Package backend startup into a single reproducible launcher with environment validation.
- Move machine-specific paths out of scripts and into config or environment variables.
- Add a proper deployment guide for Linux, macOS, and Jetson separately.
- Add health checks for camera authorization, Hugging Face login, model path validity, and serial lock state before a run starts.
- Add CI for the frontend and backend so regressions are caught before live demos.
- Publish versioned release notes and stable tagged demo configurations.
- Improve video handling by attaching the final video as a GitHub Release asset in addition to keeping a repo copy.
- Continue reducing dependency weight in teleoperation and inference paths so startup is faster and easier to debug.

## Repository Structure

| Path | Purpose |
| --- | --- |
| `backend/` | FastAPI routes and service layer |
| `frontend/` | Next.js wizard UI |
| `docs/BUG_LOG.md` | bug log and mitigation history |
| `docs/DEVELOPER_WARNINGS.md` | setup warnings and isolation guidance |
| `docs/assets/` | delivery media assets |
| `PROGRESS.md` | implementation changelog |

## License

This UI repository is released under the [MIT License](LICENSE).

Related artifacts keep their own licenses:

- the linked LeRobot fork remains under its original Apache-2.0 terms
- the Hugging Face dataset and model use the licenses declared on their Hugging Face pages
