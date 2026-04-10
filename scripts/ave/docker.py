"""Docker gate, image build, re-exec, and server management."""

import os
import subprocess
import sys

from ave.config import DOCKER_MODE_FILE, SERVER_CONTAINER


def docker_gate(script_name: str) -> None:
    env_val = os.environ.get("AVE_USE_DOCKER", "").lower()
    if env_val in ("1", "true", "yes"):
        _reexec_in_docker(script_name)
    elif env_val in ("0", "false", "no"):
        _ensure_requirements()
    elif _ask_docker_mode():
        _reexec_in_docker(script_name)
    else:
        _ensure_requirements()


def _ask_docker_mode() -> bool:
    if os.path.exists(DOCKER_MODE_FILE):
        try:
            saved = open(DOCKER_MODE_FILE).read().strip()
            if saved in ("true", "false"):
                return saved == "true"
        except OSError:
            pass
    if not sys.stdin.isatty():
        return True
    sys.stderr.write(
        "\nAVE_USE_DOCKER is not set. Choose execution mode:\n"
        "  [1] Docker (recommended) - run inside Docker container\n"
        "  [2] Host - install requirements.txt and run directly\n"
        "Choice [1]: "
    )
    sys.stderr.flush()
    try:
        answer = sys.stdin.readline().strip()
    except (EOFError, KeyboardInterrupt):
        answer = ""
    use_docker = answer != "2"
    try:
        with open(DOCKER_MODE_FILE, "w") as f:
            f.write("true" if use_docker else "false")
        print(f"Saved. To reset: rm {DOCKER_MODE_FILE}  or set AVE_USE_DOCKER=true/false.", file=sys.stderr)
    except OSError:
        pass
    return use_docker


def ensure_docker_image() -> None:
    r = subprocess.run(["docker", "image", "inspect", "ave-cloud"], capture_output=True)
    if r.returncode != 0:
        print("Building Docker image 'ave-cloud'...", file=sys.stderr)
        r2 = subprocess.run(["docker", "build", "-f", "scripts/Dockerfile.txt", "-t", "ave-cloud", "."])
        if r2.returncode != 0:
            print("Error: Docker build failed.", file=sys.stderr)
            sys.exit(1)


def _reexec_in_docker(script_name: str) -> None:
    ensure_docker_image()
    env_args: list[str] = []
    for var in (
        "AVE_API_KEY", "API_PLAN", "AVE_SECRET_KEY",
        "AVE_EVM_PRIVATE_KEY", "AVE_SOLANA_PRIVATE_KEY", "AVE_MNEMONIC",
        "AVE_BSC_RPC_URL", "AVE_ETH_RPC_URL", "AVE_BASE_RPC_URL",
    ):
        val = os.environ.get(var)
        if val:
            env_args += ["-e", f"{var}={val}"]
    result = subprocess.run([
        "docker", "run", "--rm", "--entrypoint", "python",
        "-e", "AVE_USE_DOCKER=true", "-e", "AVE_IN_SERVER=true",
        *env_args, "ave-cloud", f"scripts/{script_name}", *sys.argv[1:],
    ])
    sys.exit(result.returncode)


def _ensure_requirements() -> None:
    """Host mode: signing libs are lazy-imported, so nothing to install upfront.
    Data REST needs zero deps. Trade signing imports fail with clear error if missing."""
    pass


def server_is_running() -> bool:
    r = subprocess.run(
        ["docker", "inspect", "--format={{.State.Running}}", SERVER_CONTAINER],
        capture_output=True, text=True,
    )
    return r.returncode == 0 and r.stdout.strip() == "true"


def exec_in_server(argv: list[str]) -> None:
    result = subprocess.run(
        ["docker", "exec", SERVER_CONTAINER, "python", "scripts/ave_data_rest.py"] + list(argv),
    )
    sys.exit(result.returncode)
