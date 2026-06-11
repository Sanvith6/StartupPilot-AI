"""
StartupPilot AI — Local Development Launcher

A single entrypoint to run both the FastAPI backend and Streamlit frontend concurrently.
Handles graceful shutdowns, process terminations, and console output mapping.
"""

from __future__ import annotations

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# Color codes for pretty printing
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
END = "\033[0m"


def print_log(prefix: str, message: str, color: str = BLUE):
    """Print formatted logs to stdout."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color}[{timestamp}] {prefix:<12} | {message}{END}")


def launch_services():
    """Launch backend (FastAPI) and frontend (Streamlit) concurrently."""
    print(f"\n{BOLD}{GREEN}======================================================================{END}")
    print(f"{BOLD}{GREEN}                [START] STARTUPPILOT AI - SERVICE LAUNCHER                {END}")
    print(f"{BOLD}{GREEN}======================================================================{END}\n")
    
    root_dir = Path(__file__).resolve().parent
    
    # Use venv python if available, otherwise fallback to sys.executable
    venv_python = root_dir / "venv" / "Scripts" / "python.exe" if os.name == "nt" else root_dir / "venv" / "bin" / "python"
    python_exe = str(venv_python) if venv_python.exists() else sys.executable
    
    if venv_python.exists():
        print_log("LAUNCHER", f"Detected virtual environment python: {venv_python}", GREEN)
    else:
        print_log("LAUNCHER", f"Using current python interpreter: {sys.executable}", YELLOW)
        
    # ── Start Backend ─────────────────────────────────────────────────────────
    print_log("LAUNCHER", "Starting FastAPI Backend on port 8000...", GREEN)
    backend_cmd = [
        python_exe, "-m", "uvicorn", "backend.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ]
    
    try:
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(root_dir),
            stdout=None,  # Pipe directly to parent terminal
            stderr=None
        )
    except Exception as e:
        print_log("LAUNCHER", f"Failed to start Backend: {e}", RED)
        sys.exit(1)
        
    # Wait a moment for backend to bind to port
    time.sleep(2)
    
    # ── Start Frontend ────────────────────────────────────────────────────────
    print_log("LAUNCHER", "Starting Streamlit Frontend on port 8501...", BLUE)
    frontend_cmd = [
        python_exe, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port", "8501",
        "--server.address", "127.0.0.1"
    ]
    
    try:
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(root_dir),
            stdout=None,
            stderr=None
        )
    except Exception as e:
        print_log("LAUNCHER", f"Failed to start Frontend: {e}", RED)
        backend_proc.terminate()
        sys.exit(1)
        
    print_log("LAUNCHER", "Both services are running concurrently!", GREEN)
    print_log("LAUNCHER", f"{BOLD}Backend API:     http://localhost:8000{END}", GREEN)
    print_log("LAUNCHER", f"{BOLD}Streamlit App:   http://localhost:8501{END}", GREEN)
    print_log("LAUNCHER", "Press Ctrl+C to terminate both services.", YELLOW)
    print(f"\n{GREEN}------------------------ SERVICES CONSOLE LOGS ------------------------{END}\n")
    
    # ── Monitor Processes ─────────────────────────────────────────────────────
    try:
        while True:
            # Check if either process has stopped
            if backend_proc.poll() is not None:
                print_log("LAUNCHER", "Backend process terminated unexpectedly.", RED)
                break
            if frontend_proc.poll() is not None:
                print_log("LAUNCHER", "Frontend process terminated unexpectedly.", RED)
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print_log("LAUNCHER", "KeyboardInterrupt detected. Shutting down services...", YELLOW)
    finally:
        # Graceful shutdown of child processes
        print_log("LAUNCHER", "Terminating Backend process...", YELLOW)
        backend_proc.terminate()
        print_log("LAUNCHER", "Terminating Frontend process...", YELLOW)
        frontend_proc.terminate()
        
        # Wait for shutdown completion
        backend_proc.wait()
        frontend_proc.wait()
        
        print_log("LAUNCHER", "Shutdown complete. Good bye!", GREEN)


if __name__ == "__main__":
    launch_services()
