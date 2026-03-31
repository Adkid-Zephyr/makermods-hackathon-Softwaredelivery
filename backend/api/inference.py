"""Inference API endpoints."""

import asyncio
import json
import logging
import shutil
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.models.inference import InferenceRequest, InferenceResponse
from backend.models.system import ProcessStatus
from backend.services.config_manager import ConfigManager
from backend.services.port_lock_manager import PortInUseError, port_lock_manager
from backend.services.process_manager import process_manager

router = APIRouter()
config_manager = ConfigManager()
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
LOCAL_MODELS_DIR = WORKSPACE_ROOT / "models"
HF_LEROBOT_HOME = Path.home() / ".cache" / "huggingface" / "lerobot"
HF_HUB_MODELS_DIR = Path.home() / ".cache" / "huggingface" / "hub"
LEROBOT_SRC_DIR = WORKSPACE_ROOT / "lerobot-MakerMods-main" / "src"


def _policy_weights_look_readable(path: Path) -> bool:
    """Cheap sanity check so we don't prefer a corrupt local safetensors file."""
    model_path = path / "model.safetensors"
    try:
        file_size = model_path.stat().st_size
        with model_path.open("rb") as f:
            header = f.read(8)
    except OSError as exc:
        logging.warning("Skipping unreadable policy weights at %s: %s", model_path, exc)
        return False

    if file_size < 8 or len(header) < 8:
        logging.warning("Skipping truncated policy weights at %s (size=%s)", model_path, file_size)
        return False

    header_len = int.from_bytes(header, byteorder="little", signed=False)
    if header_len <= 0 or header_len > file_size - 8:
        logging.warning(
            "Skipping invalid safetensors header at %s (header_len=%s size=%s)",
            model_path,
            header_len,
            file_size,
        )
        return False

    return True


def _is_local_policy_dir(path: Path) -> bool:
    """Return True when a directory looks like a saved LeRobot policy."""
    return (
        path.is_dir()
        and (path / "config.json").exists()
        and (path / "model.safetensors").exists()
        and _policy_weights_look_readable(path)
    )


def _resolve_cached_policy_path(policy_path: str) -> Path | None:
    """Resolve a Hugging Face repo id to a cached snapshot directory when available."""
    if "/" not in policy_path:
        return None

    cache_root = HF_HUB_MODELS_DIR / f"models--{policy_path.replace('/', '--')}"
    snapshots_dir = cache_root / "snapshots"
    if not snapshots_dir.exists():
        return None

    candidates: list[Path] = []
    ref_path = cache_root / "refs" / "main"
    if ref_path.exists():
        try:
            revision = ref_path.read_text().strip()
        except OSError:
            revision = ""
        if revision:
            candidates.append(snapshots_dir / revision)

    try:
        candidates.extend(
            sorted(
                [p for p in snapshots_dir.iterdir() if p.is_dir()],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        )
    except OSError:
        return None

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if _is_local_policy_dir(candidate):
            return candidate

    return None


def _resolve_policy_path(policy_path: str) -> str:
    """Prefer a local policy directory when a Hub repo ID matches a downloaded model folder."""
    raw_path = Path(policy_path).expanduser()
    model_name = raw_path.name

    candidates: list[Path] = []
    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        candidates.extend(
            [
                Path.cwd() / raw_path,
                WORKSPACE_ROOT / raw_path,
            ]
        )

    cached_policy = _resolve_cached_policy_path(policy_path)
    if cached_policy is not None:
        candidates.append(cached_policy)

    if model_name:
        candidates.append(LOCAL_MODELS_DIR / model_name)

    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except FileNotFoundError:
            resolved = candidate.absolute()

        if resolved in seen:
            continue
        seen.add(resolved)

        if _is_local_policy_dir(resolved):
            logging.info("Inference policy resolved locally: %s -> %s", policy_path, resolved)
            return str(resolved)

    logging.info("Inference policy will use requested path: %s", policy_path)
    return policy_path


def _clear_existing_eval_cache(repo_id: str) -> None:
    """Inference writes eval data locally; remove stale cache so repeated runs can reuse the same repo ID."""
    cache_dir = HF_LEROBOT_HOME / repo_id
    if cache_dir.exists():
        logging.info("Removing stale inference cache: %s", cache_dir)
        shutil.rmtree(cache_dir)


def _build_inference_env(display_data: bool) -> dict[str, str]:
    """Provide a stable import path for lerobot when the backend process was started outside conda activation."""
    env: dict[str, str] = {"PYTHONPATH": str(LEROBOT_SRC_DIR)}
    if not display_data:
        env["RERUN"] = "off"
    return env


def build_inference_command(config, request: InferenceRequest) -> list[str]:
    """Build inference command from config and request.

    Inference uses lerobot-record with --policy.path and NO --teleop.* flags.
    The policy replaces the teleoperator and controls the robot autonomously.
    """
    resolved_policy_path = _resolve_policy_path(request.policy_path)
    cameras_dict = {}
    if config.mode == "bimanual":
        for idx, cam in enumerate(config.bimanual.cameras):
            camera_name = f"camera{idx + 1}" if request.model_type == "smolvla" else cam.name
            cameras_dict[camera_name] = {
                "type": "opencv",
                "index_or_path": cam.index,
                "width": cam.width,
                "height": cam.height,
                "fps": cam.fps,
            }

        bi = config.bimanual
        command = [
            sys.executable,
            "-m",
            "lerobot.scripts.lerobot_record",
            "--robot.type=bi_so101_follower",
            f"--robot.left_arm_port={bi.left_follower_port}",
            f"--robot.right_arm_port={bi.right_follower_port}",
            f"--robot.id={bi.follower_id or 'bimanual_follower'}",
            f"--robot.cameras={json.dumps(cameras_dict)}",
            f"--dataset.repo_id={request.repo_id}",
            f"--dataset.single_task={request.single_task}",
            f"--dataset.num_episodes={request.num_episodes}",
            f"--dataset.episode_time_s={request.episode_time_s}",
            "--dataset.push_to_hub=false",
            f"--display_data={str(request.display_data).lower()}",
            f"--policy.path={resolved_policy_path}",
        ]
        return command
    else:
        for idx, cam in enumerate(config.single_arm.cameras):
            camera_name = f"camera{idx + 1}" if request.model_type == "smolvla" else cam.name
            cameras_dict[camera_name] = {
                "type": "opencv",
                "index_or_path": cam.index,
                "width": cam.width,
                "height": cam.height,
                "fps": cam.fps,
            }

        sa = config.single_arm
        command = [
            sys.executable,
            "-m",
            "lerobot.scripts.lerobot_record",
            "--robot.type=so101_follower",
            f"--robot.port={sa.follower_port}",
            f"--robot.id={sa.follower_id or 'single_follower'}",
            f"--robot.cameras={json.dumps(cameras_dict)}",
            f"--dataset.repo_id={request.repo_id}",
            f"--dataset.single_task={request.single_task}",
            f"--dataset.num_episodes={request.num_episodes}",
            f"--dataset.episode_time_s={request.episode_time_s}",
            "--dataset.push_to_hub=false",
            f"--display_data={str(request.display_data).lower()}",
            f"--policy.path={resolved_policy_path}",
        ]
        return command


def _extract_inference_ports(config) -> list[str]:
    """Extract follower ports used by inference (no teleop ports needed)."""
    if config.mode == "bimanual":
        bi = config.bimanual
        return [p for p in [bi.left_follower_port, bi.right_follower_port] if p]
    else:
        return [config.single_arm.follower_port] if config.single_arm.follower_port else []


@router.post("/start", response_model=InferenceResponse)
async def start_inference(request: InferenceRequest):
    """Start policy inference (autonomous robot control)."""
    ports = []
    try:
        config = config_manager.load_config()

        # Validate config - only need robot ports and cameras (no teleop needed)
        if config.mode == "bimanual":
            if not all(
                [
                    config.bimanual.left_follower_port,
                    config.bimanual.right_follower_port,
                ]
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Bimanual mode requires both follower arm ports to be configured",
                )

            if not config.bimanual.cameras:
                raise HTTPException(
                    status_code=400, detail="No cameras configured for inference"
                )
        else:
            if not config.single_arm.follower_port:
                raise HTTPException(
                    status_code=400,
                    detail="Single arm mode requires a follower port to be configured",
                )

            if not config.single_arm.cameras:
                raise HTTPException(
                    status_code=400, detail="No cameras configured for inference"
                )

        # Acquire port locks
        ports = _extract_inference_ports(config)
        try:
            await port_lock_manager.acquire(ports, owner="inference", mode="subprocess")
        except PortInUseError as e:
            raise HTTPException(status_code=409, detail={"message": str(e), "owner": e.owner, "port": e.port})

        _clear_existing_eval_cache(request.repo_id)
        command = build_inference_command(config, request)
        env = _build_inference_env(request.display_data)
        process_id = await process_manager.start_process(command, "inference", env=env)

        # Register process→ports mapping for release on stop
        await port_lock_manager.register_process(process_id, ports)

        return InferenceResponse(
            process_id=process_id, message="Inference started successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        if ports:
            await port_lock_manager.release(ports)
        raise HTTPException(status_code=500, detail=f"Failed to start inference: {e}")


@router.post("/stop/{process_id}")
async def stop_inference(process_id: str):
    """Stop inference."""
    try:
        success = await process_manager.stop_process(process_id)

        if not success:
            raise HTTPException(
                status_code=404, detail=f"Process {process_id} not found"
            )

        # Wait for OS to release ports, then release locks
        await asyncio.sleep(0.5)
        await port_lock_manager.release_for_process(process_id)

        return {"message": "Inference stopped successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop inference: {e}")


@router.get("/status/{process_id}", response_model=ProcessStatus)
async def get_inference_status(process_id: str):
    """Get inference process status."""
    try:
        status = await process_manager.get_status(process_id)

        if not status:
            raise HTTPException(
                status_code=404, detail=f"Process {process_id} not found"
            )

        return status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {e}")
