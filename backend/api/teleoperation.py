"""Teleoperation API endpoints."""

import asyncio
import json
import sys

from fastapi import APIRouter, HTTPException

from backend.models.system import ProcessStatus
from backend.models.teleoperation import TeleoperationRequest, TeleoperationResponse
from backend.services.config_manager import ConfigManager
from backend.services.port_lock_manager import PortInUseError, port_lock_manager
from backend.services.process_manager import process_manager

router = APIRouter()
config_manager = ConfigManager()


def build_teleoperation_command(config, display_data: bool = True) -> list[str]:
    """Build teleoperation command from config."""
    script_module = "backend.scripts.lightweight_teleoperate"
    if config.mode == "bimanual":
        bi = config.bimanual
        return [
            sys.executable,
            "-m",
            script_module,
            "--mode=bimanual",
            f"--left-follower-port={bi.left_follower_port}",
            f"--right-follower-port={bi.right_follower_port}",
            f"--left-leader-port={bi.left_leader_port}",
            f"--right-leader-port={bi.right_leader_port}",
            f"--bimanual-follower-id={bi.follower_id or 'bimanual_follower'}",
            f"--bimanual-leader-id={bi.leader_id or 'bimanual_leader'}",
        ]
    else:
        sa = config.single_arm
        command = [
            sys.executable,
            "-m",
            script_module,
            "--mode=single",
            f"--follower-port={sa.follower_port}",
            f"--leader-port={sa.leader_port}",
            f"--follower-id={sa.follower_id or 'single_follower'}",
            f"--leader-id={sa.leader_id or 'single_leader'}",
        ]
        if display_data:
            command.append("--display-data")
        return command

    if display_data:
        command = [*command, "--display-data"]
    return command


def _extract_ports(config) -> list[str]:
    """Extract all serial ports from the current config."""
    if config.mode == "bimanual":
        bi = config.bimanual
        return [p for p in [
            bi.left_follower_port, bi.right_follower_port,
            bi.left_leader_port, bi.right_leader_port,
        ] if p]
    else:
        sa = config.single_arm
        return [p for p in [sa.follower_port, sa.leader_port] if p]


@router.post("/start", response_model=TeleoperationResponse)
async def start_teleoperation(request: TeleoperationRequest):
    """Start teleoperation."""
    ports = []
    try:
        config = config_manager.load_config()

        # Validate config
        if config.mode == "bimanual":
            if not all(
                [
                    config.bimanual.left_follower_port,
                    config.bimanual.left_leader_port,
                    config.bimanual.right_follower_port,
                    config.bimanual.right_leader_port,
                ]
            ):
                raise HTTPException(
                    status_code=400, detail="Bimanual mode requires all four ports to be configured"
                )
        else:
            if not all([config.single_arm.follower_port, config.single_arm.leader_port]):
                raise HTTPException(
                    status_code=400, detail="Single arm mode requires both follower and leader ports"
                )

        # Acquire port locks
        ports = _extract_ports(config)
        try:
            await port_lock_manager.acquire(ports, owner="teleoperation", mode="subprocess")
        except PortInUseError as e:
            raise HTTPException(status_code=409, detail={"message": str(e), "owner": e.owner, "port": e.port})

        command = build_teleoperation_command(config, display_data=request.display_data)
        process_id = await process_manager.start_process(
            command, "teleoperation", env={"RERUN": "off"}
        )

        # Register process→ports mapping for release on stop
        await port_lock_manager.register_process(process_id, ports)

        return TeleoperationResponse(process_id=process_id, message="Teleoperation started successfully")

    except HTTPException:
        raise
    except Exception as e:
        if ports:
            await port_lock_manager.release(ports)
        raise HTTPException(status_code=500, detail=f"Failed to start teleoperation: {e}")


@router.post("/stop/{process_id}")
async def stop_teleoperation(process_id: str):
    """Stop teleoperation."""
    try:
        success = await process_manager.stop_process(process_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Process {process_id} not found")

        # Wait for OS to release the serial ports, then release the locks
        await asyncio.sleep(0.5)
        await port_lock_manager.release_for_process(process_id)

        return {"message": "Teleoperation stopped successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop teleoperation: {e}")


@router.get("/status/{process_id}", response_model=ProcessStatus)
async def get_teleoperation_status(process_id: str):
    """Get teleoperation process status."""
    try:
        status = await process_manager.get_status(process_id)

        if not status:
            raise HTTPException(status_code=404, detail=f"Process {process_id} not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {e}")
