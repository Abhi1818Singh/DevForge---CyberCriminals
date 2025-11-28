# # patcher.py
# import os
# import re
# import subprocess
# import textwrap
# from typing import Optional, Callable, List

# from models import Patch
# from analyzer import ErrorInfo
# from runner import RunResult



# # 🆕 global context for user instruction
# CURRENT_INSTRUCTION: Optional[str] = None


# def set_instruction_context(instr: Optional[str]):
#     global CURRENT_INSTRUCTION
#     CURRENT_INSTRUCTION = instr
# # ---------- Utility: call local LLM via Ollama ----------

# def call_local_llm(prompt: str, model: Optional[str] = None, timeout: int = 120) -> str:
#     """
#     Call a local LLM using the `ollama` CLI.
#     This stays fully offline once the model is pulled.
#     """
#     model = model or os.getenv("LOCAL_LLM_MODEL", "llama3")

#     try:
#         proc = subprocess.run(
#             ["ollama", "run", model],
#             input=prompt.encode("utf-8"),
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             timeout=timeout,
#         )
#     except FileNotFoundError:
#         # ollama CLI not found
#         raise RuntimeError(
#             "Ollama not found. Install it and ensure `ollama` is in PATH."
#         )

#     stdout = proc.stdout.decode("utf-8", errors="replace")
#     stderr = proc.stderr.decode("utf-8", errors="replace")

#     if proc.returncode != 0:
#         raise RuntimeError(f"LLM call failed: {stderr or 'unknown error'}")

#     return stdout


# # ---------- Rule-based handlers ----------

# def handle_index_error(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
#     """
#     Heuristic fix for: IndexError: list index out of range
#     Pattern: arr = [...] ; for i in range(K): ... arr[i] ...
#     Change: range(K) -> range(len(arr))
#     """
#     if error.error_type != "IndexError":
#         return None
#     if "list index out of range" not in error.message:
#         return None

#     lines = code.splitlines()
#     idx = None
#     if error.line_no is not None and 1 <= error.line_no <= len(lines):
#         idx = error.line_no - 1

#     if idx is None:
#         return None

#     error_line = lines[idx]
#     # Find something like arr[i]
#     m = re.search(r"(\w+)\s*\[\s*i\s*\]", error_line)
#     if not m:
#         return None

#     arr_name = m.group(1)

#     # Find for-loop with range(K) above this line
#     loop_line_index = None
#     for j in range(idx - 1, -1, -1):
#         line = lines[j].strip()
#         m_loop = re.match(r"for\s+(\w+)\s+in\s+range\((\d+)\)\s*:", line)
#         if m_loop:
#             loop_line_index = j
#             break

#     if loop_line_index is None:
#         return None

#     old_loop_line = lines[loop_line_index]
#     new_loop_line = re.sub(
#         r"range\(\s*\d+\s*\)",
#         f"range(len({arr_name}))",
#         old_loop_line,
#     )

#     if old_loop_line == new_loop_line:
#         return None

#     new_lines = list(lines)
#     new_lines[loop_line_index] = new_loop_line
#     new_code = "\n".join(new_lines)

#     description = (
#         f"Adjusted loop range to use len({arr_name}) instead of a fixed number "
#         f"to avoid IndexError: list index out of range."
#     )

#     return Patch(
#         old_code=code,
#         new_code=new_code,
#         description=description,
#     )


# def handle_syntax_error(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
#     """
#     Simple SyntaxError fixer:
#     If the error line is a control statement without a colon, add ':'.
#     """
#     if error.error_type != "SyntaxError":
#         return None
#     if error.line_no is None:
#         return None

#     lines = code.splitlines()
#     if not (1 <= error.line_no <= len(lines)):
#         return None

#     idx = error.line_no - 1
#     line = lines[idx]

#     if ":" in line:
#         return None

#     stripped = line.strip()
#     control_keywords = (
#         "if ", "for ", "while ", "def ", "class ", "elif ", "else", "try", "except", "finally"
#     )

#     if any(stripped.startswith(kw) for kw in control_keywords):
#         new_line = line.rstrip() + ":"
#         new_lines = list(lines)
#         new_lines[idx] = new_line
#         new_code = "\n".join(new_lines)

#         return Patch(
#             old_code=code,
#             new_code=new_code,
#             description="Added missing colon at end of control statement to fix SyntaxError.",
#         )

#     return None


# def handle_name_error(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
#     """
#     Heuristic NameError fixer:
#     - Parse undefined name from error.message
#     - Find a similar identifier used elsewhere
#     - Replace undefined name with that identifier
#     """
#     if error.error_type != "NameError":
#         return None

#     m = re.search(r"name '(\w+)' is not defined", error.message)
#     if not m:
#         return None

#     undefined_name = m.group(1)

#     # Find all identifiers
#     identifiers = set(re.findall(r"\b[A-Za-z_]\w*\b", code))

#     python_keywords = {
#         "if", "else", "elif", "for", "while", "try", "except", "finally", "class",
#         "def", "return", "import", "from", "as", "with", "in", "is", "not", "and",
#         "or", "True", "False", "None", "break", "continue", "pass", "lambda", "yield",
#         "global", "nonlocal", "del", "assert", "raise",
#     }
#     candidates = [name for name in identifiers if name not in python_keywords]

#     if undefined_name in candidates:
#         candidates.remove(undefined_name)

#     if not candidates:
#         return None

#     # Score by common prefix length
#     def score(candidate: str) -> int:
#         common = 0
#         for a, b in zip(candidate, undefined_name):
#             if a == b:
#                 common += 1
#             else:
#                 break
#         return common

#     best = max(candidates, key=score)
#     if score(best) == 0:
#         return None

#     new_code = re.sub(rf"\b{undefined_name}\b", best, code)

#     if new_code == code:
#         return None

#     description = (
#         f"Replaced undefined name '{undefined_name}' with '{best}' to fix NameError."
#     )

#     return Patch(
#         old_code=code,
#         new_code=new_code,
#         description=description,
#     )


# def handle_type_error_wrong_args(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
#     """
#     Heuristic for TypeError like:
#       foo() takes 2 positional arguments but 3 were given

#     Strategy:
#     - Parse function name and expected/given arg count.
#     - Find a call to that function on the error line.
#     - If too many args: drop the last args.
#     """
#     if error.error_type != "TypeError":
#         return None

#     msg = error.message
#     m = re.search(r"(\w+)\(\) takes (\d+) positional arguments but (\d+) were given", msg)
#     if not m:
#         return None

#     func_name = m.group(1)
#     expected = int(m.group(2))
#     given = int(m.group(3))

#     if given <= expected:
#         return None  # only handle 'too many args' safely

#     if error.line_no is None:
#         return None

#     lines = code.splitlines()
#     if not (1 <= error.line_no <= len(lines)):
#         return None

#     idx = error.line_no - 1
#     line = lines[idx]

#     call_pattern = rf"{func_name}\s*\((.*)\)"
#     m_call = re.search(call_pattern, line)
#     if not m_call:
#         return None

#     args_str = m_call.group(1)
#     args = [a.strip() for a in args_str.split(",") if a.strip()]
#     if len(args) != given:
#         return None

#     new_args = args[:expected]
#     new_args_str = ", ".join(new_args)
#     new_line = re.sub(call_pattern, f"{func_name}({new_args_str})", line)

#     new_lines = list(lines)
#     new_lines[idx] = new_line
#     new_code = "\n".join(new_lines)

#     description = (
#         f"Reduced arguments in call to '{func_name}' from {given} to {expected} to fix TypeError."
#     )

#     return Patch(
#         old_code=code,
#         new_code=new_code,
#         description=description,
#     )


# def handle_zero_division_error(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
#     """
#     Heuristic for ZeroDivisionError.
#     Wrap the division with a denominator != 0 check.
#     """
#     if error.error_type != "ZeroDivisionError":
#         return None
#     if error.line_no is None:
#         return None

#     lines = code.splitlines()
#     if not (1 <= error.line_no <= len(lines)):
#         return None

#     idx = error.line_no - 1
#     line = lines[idx]

#     # Look for something like "X / Y" or "X // Y"
#     m = re.search(r"(.+?)(/|//)\s*([A-Za-z_]\w*)", line)
#     if not m:
#         return None

#     left_expr = m.group(1).strip()
#     op = m.group(2)
#     denom = m.group(3).strip()

#     guarded = f"({left_expr} {op} {denom} if {denom} != 0 else 0)"

#     new_line = line[:m.start()] + guarded + line[m.end():]

#     new_lines = list(lines)
#     new_lines[idx] = new_line
#     new_code = "\n".join(new_lines)

#     description = (
#         f"Wrapped division by '{denom}' with a zero check to fix ZeroDivisionError."
#     )

#     return Patch(
#         old_code=code,
#         new_code=new_code,
#         description=description,
#     )



# def handle_name_error_move_func(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
#     if error.error_type != "NameError":
#         return None

#     m = re.search(r"name '(\w+)' is not defined", error.message)
#     if not m:
#         return None

#     fn_name = m.group(1)

#     lines = code.splitlines()

#     # Find function definition
#     def_start = None
#     def_end = None

#     for i, line in enumerate(lines):
#         if line.strip().startswith(f"def {fn_name}("):
#             def_start = i
#             # find end of function by dedent
#             for j in range(i+1, len(lines)):
#                 if lines[j].strip().startswith("def ") or lines[j].strip().startswith("if __name__"):
#                     def_end = j
#                     break
#             if def_end is None:
#                 def_end = len(lines)
#             break

#     if def_start is None:
#         return None  # function definition missing entirely

#     # Extract that function's code
#     func_block = lines[def_start:def_end]

#     # Remove original block
#     remaining = lines[:def_start] + lines[def_end:]

#     # Insert function ABOVE main_process or before __main__
#     insert_pos = 0
#     for k, line in enumerate(remaining):
#         if line.strip().startswith("def main_process"):
#             insert_pos = k
#             break

#     new_lines = remaining[:insert_pos] + func_block + [""] + remaining[insert_pos:]
#     new_code = "\n".join(new_lines)

#     return Patch(
#         old_code=code,
#         new_code=new_code,
#         description=f"Moved function '{fn_name}' definition above its first usage to fix NameError."
#     )





# def handle_module_not_found_error(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
#     """
#     Fix ModuleNotFoundError by commenting out the missing import.

#     Example:
#         ModuleNotFoundError: No module named 'quantum_encryption_lib'
#     We turn:
#         import quantum_encryption_lib
#     into:
#         # import quantum_encryption_lib  # disabled: module not available
#     """
#     if error.error_type != "ModuleNotFoundError":
#         return None

#     m = re.search(r"No module named '([^']+)'", error.message)
#     if not m:
#         return None

#     missing_module = m.group(1)

#     lines = code.splitlines()
#     changed = False

#     for i, line in enumerate(lines):
#         stripped = line.strip()
#         if stripped.startswith(f"import {missing_module}") or stripped.startswith(f"from {missing_module} import"):
#             # Comment out this line
#             if not stripped.startswith("#"):
#                 lines[i] = "# " + line + f"  # disabled: module '{missing_module}' not available"
#                 changed = True

#     if not changed:
#         return None

#     new_code = "\n".join(lines)

#     return Patch(
#         old_code=code,
#         new_code=new_code,
#         description=f"Commented out missing module import '{missing_module}' to fix ModuleNotFoundError.",
#     )




# def handle_name_error_dunder_name_main(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
#     """
#     Fix common typo:
#         if _name_ == "_main_":
#     should be:
#         if __name__ == "__main__":
#     Triggered when NameError is for '_name_'.
#     """
#     if error.error_type != "NameError":
#         return None

#     # Only handle the special case for _name_
#     if "name '_name_'" not in error.message:
#         return None

#     lines = code.splitlines()
#     changed = False

#     for i, line in enumerate(lines):
#         if "_name_" in line:
#             new_line = line.replace("_name_", "__name__")
#             # also fix "_main_" if present
#             new_line = new_line.replace('"__main_"', '"__main__"').replace('" _main_ "', '"__main__"')
#             new_line = new_line.replace('_main_', '__main__')
#             lines[i] = new_line
#             changed = True

#     if not changed:
#         return None

#     new_code = "\n".join(lines)

#     return Patch(
#         old_code=code,
#         new_code=new_code,
#         description="Fixed typo `_name_` / `_main_` to proper `__name__` / `\"__main__\"`.",
#     )





# def handle_bad_init_typo(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
#     """
#     Fix common constructor typo:
#       def _init_(self):
#     should be:
#       def __init__(self):
#     Triggered when AttributeError suggests missing initialization attributes.
#     """
#     if error.error_type != "AttributeError":
#         return None

#     # Look for _init_ definition
#     lines = code.splitlines()
#     changed = False

#     for i, line in enumerate(lines):
#         if "def _init_(" in line:
#             lines[i] = line.replace("_init_", "__init__")
#             changed = True

#     if not changed:
#         return None

#     return Patch(
#         old_code=code,
#         new_code="\n".join(lines),
#         description="Fixed constructor typo `_init_` to `__init__` to initialize attributes properly."
#     )



# # ---------- LLM fallback handler ----------



# def extract_code_from_llm_output(raw: str) -> str:
#     """
#     Try to extract pure Python code from the LLM output.
#     Handles cases like:
#       - Plain code
#       - Code wrapped in ```python ... ```
#       - Explanations like 'Here is the fixed Python code:' before the code.
#     """
#     text = raw.strip()

#     # Case 1: fenced code block with ```
#     if "```" in text:
#         parts = text.split("```")
#         # Typical pattern: "some text\n```python\ncode\n```"
#         # parts = ["some text\n", "python\ncode\n", ""]
#         code_block = None

#         for part in parts[1:]:
#             lower = part.lower()
#             if "python" in lower:
#                 # Drop the first line ("python") and keep the rest
#                 lines = part.splitlines()
#                 if lines and "python" in lines[0].lower():
#                     lines = lines[1:]
#                 code_block = "\n".join(lines)
#                 break

#         # If we didn't find an explicit "python" tag, maybe just ```code```
#         if code_block is None and len(parts) >= 2:
#             code_block = parts[1]

#         if code_block is not None:
#             return code_block.strip()

#     # Case 2: no fences – strip obvious explanation lines
#     lines = text.splitlines()
#     cleaned_lines = []
#     for line in lines:
#         stripped = line.strip()
#         if stripped.lower().startswith("here is the fixed python code"):
#             continue
#         if stripped.lower().startswith("here is the corrected code"):
#             continue
#         if stripped.lower().startswith("fixed code"):
#             continue
#         if stripped.lower().startswith("corrected code"):
#             continue
#         cleaned_lines.append(line)

#     return "\n".join(cleaned_lines).strip()

# def handle_with_local_llm(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
#     """
#     Generic fallback using a local LLM (via Ollama).

#     Strategy:
#     - Let the rule-based handlers handle simple & common cases quickly.
#     - When we reach here, we ask the LLM to do a FULL, AGGRESSIVE cleanup:
#       * fix ALL runtime + logical issues it can detect
#       * clean useless comments / bug markers / placeholder code
#       * keep behavior aligned with original intent.
#     """
#     user_goal = CURRENT_INSTRUCTION or (
#         "Fix ALL problems in this Python code and clean it up. "
#         "Make it run correctly and remove useless comments or dead code."
#     )

#     prompt = f"""
# You are a senior Python engineer repairing a broken script.

# User goal:
# {user_goal}

# Your tasks (very important):
# 1. Fix ALL issues you can find in the code:
#    - not only the first error from the traceback,
#    - but also other obvious bugs (NameError, AttributeError, wrong __init__, __dict__,
#      bad imports, wrong method calls, bad types, infinite loops, etc.).
# 2. Make the script directly runnable with Python without crashing for normal usage.
# 3. Clean and simplify the code:
#    - REMOVE hackathon hints, BUG comments, placeholder comments, commented-out broken code,
#      and any other useless or noisy comments.
#    - You MAY keep short, helpful comments that explain non-trivial logic.
# 4. You MAY:
#    - reorder function / class definitions if needed,
#    - adjust function signatures and names if you update all their usages consistently,
#    - add small helper functions or constants,
#    - replace placeholder logic with a reasonable, working implementation,
#    - but keep the overall behavior and intent of the script consistent with the original.

# Input code:
# === ORIGINAL CODE START ===
# {code}
# === ORIGINAL CODE END ===

# Python error output from running the code (may show only the first error):
# === ERROR OUTPUT START ===
# {run_result.stderr}
# === ERROR OUTPUT END ===

# Now produce the FINAL, CLEANED, CORRECT Python source code.

# Rules for your answer:
# - RETURN ONLY the Python code.
# - NO explanations.
# - NO markdown.
# - NO ``` fences.
# - NO prose like "Here is the fixed code".
# """

#     try:
#         raw = call_local_llm(textwrap.dedent(prompt))
#     except Exception as e:
#         print(f"[LLM handler] Error calling local LLM: {e}")
#         return None

#     new_code = extract_code_from_llm_output(raw)

#     if not new_code:
#         return None

#     # If the LLM gives back essentially the same code, treat as no-op
#     if new_code.strip() == code.strip():
#         return None

#     return Patch(
#         old_code=code,
#         new_code=new_code,
#         description="Repaired (and cleaned) by local LLM model (Ollama).",
#     )


# # ---------- Handler registry ----------
# HANDLERS: List[Callable[[str, ErrorInfo, RunResult], Optional[Patch]]] = [
#     handle_index_error,
#     handle_syntax_error,
#     handle_type_error_wrong_args,
#     handle_zero_division_error,
#     handle_module_not_found_error,
#     # handle_name_error,  # 🔴 DISABLED: too risky for big real code
#     handle_with_local_llm,  # generic AI fallback (handles NameError too)
#      handle_name_error_move_func,  # 🆕 Run BEFORE LLM
#      handle_name_error_dunder_name_main,
#      handle_bad_init_typo,


#       # 🔚 finally, the generic catch-all LLM fallback
#     handle_with_local_llm,
# ]


# def generate_patch(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
#     for handler in HANDLERS:
#         patch = handler(code, error, run_result)
#         if patch is not None:
#             return patch
#     return None





# patcher.py
import os
import re
import subprocess
import textwrap
from typing import Optional, Callable, List

from models import Patch
from analyzer import ErrorInfo
from runner import RunResult

# ---------- Global instruction context (optional user request) ----------

CURRENT_INSTRUCTION: Optional[str] = None


def set_instruction_context(instr: Optional[str]):
    """
    Called from controller.repair_code() to tell the patcher
    what the user wants (optional).
    """
    global CURRENT_INSTRUCTION
    CURRENT_INSTRUCTION = instr


# ---------- Utility: call local LLM via Ollama ----------

def call_local_llm(prompt: str, model: Optional[str] = None, timeout: int = 120) -> str:
    """
    Call a local LLM using the `ollama` CLI.
    This stays fully offline once the model is pulled.
    """
    model = model or os.getenv("LOCAL_LLM_MODEL", "llama3")

    try:
        proc = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except FileNotFoundError:
        # ollama CLI not found
        raise RuntimeError(
            "Ollama not found. Install it and ensure `ollama` is in PATH."
        )

    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")

    if proc.returncode != 0:
        raise RuntimeError(f"LLM call failed: {stderr or 'unknown error'}")

    return stdout


def extract_code_from_llm_output(raw: str) -> str:
    """
    Try to extract pure Python code from the LLM output.
    Handles:
      - Plain code
      - ```python ... ``` blocks
      - Leading explanation lines.
    """
    text = raw.strip()

    # Case 1: fenced code block
    if "```" in text:
        parts = text.split("```")
        code_block = None

        # Look for something like: ```python\ncode\n```
        for part in parts[1:]:
            lower = part.lower()
            if "python" in lower:
                lines = part.splitlines()
                if lines and "python" in lines[0].lower():
                    lines = lines[1:]
                code_block = "\n".join(lines)
                break

        # If no explicit python tag, take the first block
        if code_block is None and len(parts) >= 2:
            code_block = parts[1]

        if code_block is not None:
            return code_block.strip()

    # Case 2: no fences – strip obvious explanation lines
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        s = line.strip().lower()
        if s.startswith("here is the fixed python code"):
            continue
        if s.startswith("here is the corrected code"):
            continue
        if s.startswith("fixed code"):
            continue
        if s.startswith("corrected code"):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


# ---------- Rule-based handlers (fast, simple fixes) ----------

def handle_index_error(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
    """
    Heuristic fix for: IndexError: list index out of range
    Pattern: arr = [...] ; for i in range(K): ... arr[i] ...
    Change: range(K) -> range(len(arr))
    """
    if error.error_type != "IndexError":
        return None
    if "list index out of range" not in error.message:
        return None

    lines = code.splitlines()
    idx = None
    if error.line_no is not None and 1 <= error.line_no <= len(lines):
        idx = error.line_no - 1

    if idx is None:
        return None

    error_line = lines[idx]
    # Find something like arr[i]
    m = re.search(r"(\w+)\s*\[\s*i\s*\]", error_line)
    if not m:
        return None

    arr_name = m.group(1)

    # Find for-loop with range(K) above this line
    loop_line_index = None
    for j in range(idx - 1, -1, -1):
        line = lines[j].strip()
        m_loop = re.match(r"for\s+(\w+)\s+in\s+range\((\d+)\)\s*:", line)
        if m_loop:
            loop_line_index = j
            break

    if loop_line_index is None:
        return None

    old_loop_line = lines[loop_line_index]
    new_loop_line = re.sub(
        r"range\(\s*\d+\s*\)",
        f"range(len({arr_name}))",
        old_loop_line,
    )

    if old_loop_line == new_loop_line:
        return None

    new_lines = list(lines)
    new_lines[loop_line_index] = new_loop_line
    new_code = "\n".join(new_lines)

    description = (
        f"Adjusted loop range to use len({arr_name}) instead of a fixed number "
        f"to avoid IndexError: list index out of range."
    )

    return Patch(
        old_code=code,
        new_code=new_code,
        description=description,
    )


def handle_syntax_error(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
    """
    Simple SyntaxError fixer:
    If the error line is a control statement without a colon, add ':'.
    """
    if error.error_type != "SyntaxError":
        return None
    if error.line_no is None:
        return None

    lines = code.splitlines()
    if not (1 <= error.line_no <= len(lines)):
        return None

    idx = error.line_no - 1
    line = lines[idx]

    if ":" in line:
        return None

    stripped = line.strip()
    control_keywords = (
        "if ", "for ", "while ", "def ", "class ", "elif ", "else", "try", "except", "finally"
    )

    if any(stripped.startswith(kw) for kw in control_keywords):
        new_line = line.rstrip() + ":"
        new_lines = list(lines)
        new_lines[idx] = new_line
        new_code = "\n".join(new_lines)

        return Patch(
            old_code=code,
            new_code=new_code,
            description="Added missing colon at end of control statement to fix SyntaxError.",
        )

    return None


def handle_type_error_wrong_args(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
    """
    Heuristic for TypeError like:
      foo() takes 2 positional arguments but 3 were given
    """
    if error.error_type != "TypeError":
        return None

    msg = error.message
    m = re.search(r"(\w+)\(\) takes (\d+) positional arguments but (\d+) were given", msg)
    if not m:
        return None

    func_name = m.group(1)
    expected = int(m.group(2))
    given = int(m.group(3))

    if given <= expected:
        return None  # only handle 'too many args' safely

    if error.line_no is None:
        return None

    lines = code.splitlines()
    if not (1 <= error.line_no <= len(lines)):
        return None

    idx = error.line_no - 1
    line = lines[idx]

    call_pattern = rf"{func_name}\s*\((.*)\)"
    m_call = re.search(call_pattern, line)
    if not m_call:
        return None

    args_str = m_call.group(1)
    args = [a.strip() for a in args_str.split(",") if a.strip()]
    if len(args) != given:
        return None

    new_args = args[:expected]
    new_args_str = ", ".join(new_args)
    new_line = re.sub(call_pattern, f"{func_name}({new_args_str})", line)

    new_lines = list(lines)
    new_lines[idx] = new_line
    new_code = "\n".join(new_lines)

    description = (
        f"Reduced arguments in call to '{func_name}' from {given} to {expected} to fix TypeError."
    )

    return Patch(
        old_code=code,
        new_code=new_code,
        description=description,
    )


def handle_zero_division_error(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
    """
    Heuristic for ZeroDivisionError.
    Wrap the division with a denominator != 0 check.
    """
    if error.error_type != "ZeroDivisionError":
        return None
    if error.line_no is None:
        return None

    lines = code.splitlines()
    if not (1 <= error.line_no <= len(lines)):
        return None

    idx = error.line_no - 1
    line = lines[idx]

    # Look for something like "X / Y" or "X // Y"
    m = re.search(r"(.+?)(/|//)\s*([A-Za-z_]\w*)", line)
    if not m:
        return None

    left_expr = m.group(1).strip()
    op = m.group(2)
    denom = m.group(3).strip()

    guarded = f"({left_expr} {op} {denom} if {denom} != 0 else 0)"

    new_line = line[:m.start()] + guarded + line[m.end():]

    new_lines = list(lines)
    new_lines[idx] = new_line
    new_code = "\n".join(new_lines)

    description = (
        f"Wrapped division by '{denom}' with a zero check to fix ZeroDivisionError."
    )

    return Patch(
        old_code=code,
        new_code=new_code,
        description=description,
    )


def handle_module_not_found_error(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
    """
    Fix ModuleNotFoundError by commenting out the missing import.
    """
    if error.error_type != "ModuleNotFoundError":
        return None

    m = re.search(r"No module named '([^']+)'", error.message)
    if not m:
        return None

    missing_module = m.group(1)

    lines = code.splitlines()
    changed = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(f"import {missing_module}") or stripped.startswith(f"from {missing_module} import"):
            if not stripped.startswith("#"):
                lines[i] = "# " + line + f"  # disabled: module '{missing_module}' not available"
                changed = True

    if not changed:
        return None

    new_code = "\n".join(lines)

    return Patch(
        old_code=code,
        new_code=new_code,
        description=f"Commented out missing module import '{missing_module}' to fix ModuleNotFoundError.",
    )


def handle_name_error_dunder_name_main(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
    """
    Fix common typo:
        if _name_ == "_main_":
    should be:
        if __name__ == "__main__":
    """
    if error.error_type != "NameError":
        return None

    if "name '_name_'" not in error.message:
        return None

    lines = code.splitlines()
    changed = False

    for i, line in enumerate(lines):
        if "_name_" in line or "_main_" in line:
            new_line = line.replace("_name_", "__name__")
            new_line = new_line.replace("_main_", "__main__")
            lines[i] = new_line
            changed = True

    if not changed:
        return None

    new_code = "\n".join(lines)

    return Patch(
        old_code=code,
        new_code=new_code,
        description="Fixed typo `_name_` / `_main_` to proper `__name__` / `\"__main__\"`.",
    )


def handle_bad_init_typo(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
    """
    Fix constructor typo:
      def _init_(self):
    -> def __init__(self):
    """
    if error.error_type != "AttributeError":
        return None

    lines = code.splitlines()
    changed = False

    for i, line in enumerate(lines):
        if "def _init_(" in line:
            lines[i] = line.replace("_init_", "__init__")
            changed = True

    if not changed:
        return None

    new_code = "\n".join(lines)

    return Patch(
        old_code=code,
        new_code=new_code,
        description="Fixed constructor typo `_init_` to `__init__`.",
    )


# ---------- LLM fallback handler ----------

def handle_with_local_llm(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
    """
    Generic fallback using a local LLM (via Ollama).

    Primary goal:
      - Fix ALL errors (syntax, runtime, logic) so the program runs without exceptions.
      - Clean the code: remove useless bug comments, commented-out code, and temporary debug prints.
    """
    base_goal = (
        "Fix all syntax, runtime, and logical errors so this Python program runs to completion "
        "without throwing exceptions. Clean up the code by removing unnecessary comments "
        "that only describe bugs, commented-out code that is not used, and temporary debug "
        "print statements, unless they are clearly required for the program's behavior."
    )

    extra = ""
    if CURRENT_INSTRUCTION:
        extra = f"\nAdditionally, follow this user request: {CURRENT_INSTRUCTION}\n"

    prompt = f"""
You are a strict Python code repair engine.

PRIMARY GOAL (must always be satisfied):
{base_goal}
{extra}

Your job:
- Take the FULL Python source code and the error output from running it.
- Return a FULLY FIXED version of the code that satisfies the primary goal.

Rules:
- Keep the overall intent and behavior of the program the same unless explicitly instructed.
- Fix ALL issues: syntax errors, NameError, AttributeError, wrong __init__, type issues,
  missing imports, incorrect methods, infinite loops, etc.
- If external dependencies like mysql, tabulate, or pyfiglet are not available,
  you may remove or replace them with simple placeholder logic so that the code runs offline.
- The code must be directly runnable with Python.
- REMOVE bug-description comments and dead/commented-out code that is no longer needed.
- DO NOT write explanations, comments, or markdown.
- Return ONLY the final Python code.


=== ORIGINAL CODE START ===
{code}
=== ORIGINAL CODE END ===

=== ERROR OUTPUT START ===
{run_result.stderr}
=== ERROR OUTPUT END ===

Now respond with ONLY the corrected full Python code.
"""

    try:
        raw = call_local_llm(textwrap.dedent(prompt))
    except Exception as e:
        print(f"[LLM handler] Error calling local LLM: {e}")
        return None

    new_code = extract_code_from_llm_output(raw)

    if not new_code:
        return None

    if new_code.strip() == code.strip():
        return None

    return Patch(
        old_code=code,
        new_code=new_code,
        description="Repaired and cleaned by local LLM model (Ollama).",
    )


# ---------- Handler registry & main entry ----------

HANDLERS: List[Callable[[str, ErrorInfo, RunResult], Optional[Patch]]] = [
    handle_index_error,
    handle_syntax_error,
    handle_type_error_wrong_args,
    handle_zero_division_error,
    # handle_module_not_found_error,
    handle_name_error_dunder_name_main,
    handle_bad_init_typo,
    handle_with_local_llm,  # last: generic fallback
]


def generate_patch(code: str, error: ErrorInfo, run_result: RunResult) -> Optional[Patch]:
    """
    Try each handler in order until one returns a Patch.
    """
    for handler in HANDLERS:
        patch = handler(code, error, run_result)
        if patch is not None:
            return patch
    return None
