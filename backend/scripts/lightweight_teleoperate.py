"""Lightweight teleoperation runner that avoids the heavy LeRobot CLI import chain.

This script is used by the web UI to run leader->follower teleoperation without
importing the full `lerobot_teleoperate.py` stack, which currently pulls in
torch/torchvision/rerun/huggingface modules that are not needed for basic arm
teleoperation and can crash on this machine.
"""

from __future__ import annotations

import argparse
import logging
import signal
import time
from pathlib import Path

from lerobot.robots.bi_so101_follower import BiSO101Follower, BiSO101FollowerConfig
from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
from lerobot.teleoperators.bi_so101_leader import BiSO101Leader, BiSO101LeaderConfig
from lerobot.teleoperators.so101_leader import SO101Leader, SO101LeaderConfig
from lerobot.utils.robot_utils import busy_wait


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run lightweight SO101 teleoperation")
    parser.add_argument("--mode", choices=["single", "bimanual"], required=True)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--display-data", action="store_true")

    parser.add_argument("--follower-port")
    parser.add_argument("--leader-port")
    parser.add_argument("--follower-id")
    parser.add_argument("--leader-id")

    parser.add_argument("--left-follower-port")
    parser.add_argument("--right-follower-port")
    parser.add_argument("--left-leader-port")
    parser.add_argument("--right-leader-port")
    parser.add_argument("--bimanual-follower-id")
    parser.add_argument("--bimanual-leader-id")
    return parser.parse_args()


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(asctime)s %(message)s",
    )


def _build_single(args: argparse.Namespace) -> tuple[SO101Leader, SO101Follower]:
    if not args.leader_port or not args.follower_port:
        raise ValueError("Single mode requires leader and follower ports")

    leader = SO101Leader(
        SO101LeaderConfig(
            port=args.leader_port,
            id=args.leader_id,
        )
    )
    follower = SO101Follower(
        SO101FollowerConfig(
            port=args.follower_port,
            id=args.follower_id,
            cameras={},
        )
    )
    return leader, follower


def _build_bimanual(args: argparse.Namespace) -> tuple[BiSO101Leader, BiSO101Follower]:
    required = [
        args.left_leader_port,
        args.right_leader_port,
        args.left_follower_port,
        args.right_follower_port,
    ]
    if not all(required):
        raise ValueError("Bimanual mode requires all four ports")

    leader = BiSO101Leader(
        BiSO101LeaderConfig(
            left_arm_port=args.left_leader_port,
            right_arm_port=args.right_leader_port,
            id=args.bimanual_leader_id,
        )
    )
    follower = BiSO101Follower(
        BiSO101FollowerConfig(
            left_arm_port=args.left_follower_port,
            right_arm_port=args.right_follower_port,
            id=args.bimanual_follower_id,
            cameras={},
        )
    )
    return leader, follower


def main() -> int:
    args = _parse_args()
    _configure_logging()

    if args.display_data:
        logging.info("display_data requested, but lightweight teleop runs without Rerun visualization")

    stop_requested = False

    def _handle_signal(signum, _frame):
        nonlocal stop_requested
        logging.info("Received signal %s, stopping teleoperation", signum)
        stop_requested = True

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    if args.mode == "single":
        leader, follower = _build_single(args)
    else:
        leader, follower = _build_bimanual(args)

    logging.info("Connecting teleoperator...")
    leader.connect()
    logging.info("%s connected", leader)

    logging.info("Connecting follower...")
    follower.connect()
    logging.info("%s connected", follower)

    loop_count = 0
    started = time.perf_counter()
    last_report = started

    try:
        while not stop_requested:
            tick_start = time.perf_counter()
            action = leader.get_action()
            follower.send_action(action)
            loop_count += 1

            now = time.perf_counter()
            if now - last_report >= 1.0:
                hz = loop_count / max(now - started, 1e-6)
                logging.info("Teleoperation running at %.1f Hz", hz)
                last_report = now

            busy_wait((1 / args.fps) - (time.perf_counter() - tick_start))
    finally:
        errors: list[str] = []

        try:
            leader.disconnect()
        except Exception as exc:  # pragma: no cover - cleanup best effort
            errors.append(f"leader disconnect failed: {exc}")

        try:
            follower.disconnect()
        except Exception as exc:  # pragma: no cover - cleanup best effort
            errors.append(f"follower disconnect failed: {exc}")

        for error in errors:
            logging.warning(error)

        logging.info("Teleoperation stopped")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
