# # analyzer.py
# import re
# from dataclasses import dataclass
# from typing import Optional
# from runner import RunResult


# @dataclass
# class ErrorInfo:
#     """Structured info about what went wrong in a run."""
#     error_type: Optional[str]   # e.g. "IndexError", "SyntaxError", "Timeout"
#     message: str                # the error message
#     line_no: Optional[int]      # line number in the user code, if we can parse it
#     is_timeout: bool = False


# def analyze_run_result(run_result: RunResult) -> Optional[ErrorInfo]:
#     """
#     Look at RunResult and extract error type, message, line number.
#     Return None if no clear error (e.g., wrong output but no exception).
#     """
#     # Handle timeout explicitly
#     if run_result.timeout:
#         return ErrorInfo(
#             error_type="Timeout",
#             message="Execution timed out.",
#             line_no=None,
#             is_timeout=True,
#         )

#     # If success and no stderr -> no error
#     if run_result.success and not run_result.stderr.strip():
#         return None

#     stderr = run_result.stderr.strip()
#     if not stderr:
#         return None

#     # Try to find the last "File ..., line X" to get line number
#     line_no = None
#     for line in stderr.splitlines():
#         m = re.search(r"line (\d+)", line)
#         if m:
#             try:
#                 line_no = int(m.group(1))
#             except ValueError:
#                 pass

#     # The last line usually contains "ErrorType: message"
#     last_line = stderr.splitlines()[-1]
#     error_type = None
#     message = last_line

#     m = re.match(r"(\w+Error):\s*(.*)", last_line)
#     if m:
#         error_type = m.group(1)       # e.g. IndexError
#         message = m.group(2) or ""    # e.g. list index out of range

#     return ErrorInfo(
#         error_type=error_type,
#         message=message,
#         line_no=line_no,
#         is_timeout=False,
#     )


# analyzer.py
import re
from dataclasses import dataclass
from typing import Optional
from runner import RunResult


@dataclass
class ErrorInfo:
    """
    Parsed error information from a failed run.
    """
    error_type: Optional[str]   # e.g. "IndexError", "SyntaxError", "Timeout"
    message: str                # e.g. "list index out of range"
    line_no: Optional[int]      # 1-based line number
    is_timeout: bool = False


def analyze_run_result(run_result: RunResult) -> Optional[ErrorInfo]:
    """
    Inspect RunResult and extract structured error info.
    Return None if we can’t detect a specific error.
    """
    # Timeout
    if run_result.timeout:
        return ErrorInfo(
            error_type="Timeout",
            message="Execution timed out.",
            line_no=None,
            is_timeout=True,
        )

    stderr = (run_result.stderr or "").strip()
    if not stderr:
        # No stderr and not timeout → maybe wrong output, but not an exception
        return None

    # Try to extract line number from "File ..., line X"
    line_no = None
    for line in stderr.splitlines():
        m = re.search(r"line (\d+)", line)
        if m:
            try:
                line_no = int(m.group(1))
            except ValueError:
                pass

    # Last line usually has "ErrorType: message"
    last_line = stderr.splitlines()[-1]
    error_type = None
    message = last_line

    m = re.match(r"(\w+Error):\s*(.*)", last_line)
    if m:
        error_type = m.group(1)
        message = m.group(2) or ""

    return ErrorInfo(
        error_type=error_type,
        message=message,
        line_no=line_no,
        is_timeout=False,
    )
