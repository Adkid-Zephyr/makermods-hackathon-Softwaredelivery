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
