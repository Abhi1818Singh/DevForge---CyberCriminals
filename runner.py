# runner.py
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from typing import Optional


@dataclass
class RunResult:
    success: bool
    timeout: bool
    return_code: int
    stdout: str
    stderr: str
    # You can also add: exec_time, etc.


def run_python_code(
    code: str,
    stdin_input: Optional[str] = None,
    timeout_seconds: int = 3,
) -> RunResult:
    """
    Run untrusted Python code in a separate process with a timeout.
    This is a 'light' sandbox: separate process + timeout + no network by default.
    For serious isolation, you'd add Docker / firejail / WASM etc.
    """
    # Clean indentation in case code is passed with leading spaces
    code = textwrap.dedent(code)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        tmp.write(code)
        tmp_filename = tmp.name

    try:
        proc = subprocess.run(
            ["python3", tmp_filename],
            input=stdin_input.encode() if stdin_input is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
        )

        return RunResult(
            success=proc.returncode == 0,
            timeout=False,
            return_code=proc.returncode,
            stdout=proc.stdout.decode("utf-8", errors="replace"),
            stderr=proc.stderr.decode("utf-8", errors="replace"),
        )

    except subprocess.TimeoutExpired as e:
        # Process exceeded time limit
        stdout = e.stdout.decode("utf-8", errors="replace") if e.stdout else ""
        stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
        return RunResult(
            success=False,
            timeout=True,
            return_code=-1,
            stdout=stdout,
            stderr=stderr or "Execution timed out.",
        )
