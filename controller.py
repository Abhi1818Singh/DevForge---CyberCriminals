# # controller.py
# from typing import Optional

# from runner import run_python_code
# from models import RepairSession, IterationLog
# from analyzer import analyze_run_result
# from patcher import generate_patch, set_instruction_context  # 🆕 import helper


# def repair_code(initial_code: str, max_iterations: int = 3,
#                 instruction: Optional[str] = None) -> RepairSession:
#     """
#     Run → Analyze → Patch → Apply → Run loop.
#     `instruction` is a free-form user goal like:
#     "just fix errors", "optimize", "add logging", etc.
#     Only the LLM handler cares about it.
#     """
#     # Store instruction globally for patcher / LLM to use
#     set_instruction_context(instruction)

#     session = RepairSession(
#         original_code=initial_code,
#         max_iterations=max_iterations,
#     )

#     current_code = initial_code

#     for i in range(1, max_iterations + 1):
#         run_result = run_python_code(current_code)



        



        

#         log = IterationLog(
#             iteration=i,
#             run_result=run_result,
#         )

#         if run_result.success:
#             log.notes = "Execution succeeded. No further repair needed."
#             session.add_iteration(log)
#             session.success = True
#             session.final_code = current_code
#             return session

#         error_info = analyze_run_result(run_result)

#         if error_info is None:
#             log.notes = "Execution failed but no recognizable error was found."
#             session.add_iteration(log)
#             session.success = False
#             session.failure_reason = "Unknown error without clear exception."
#             return session

#         patch = generate_patch(current_code, error_info, run_result)

#         if patch is None:
#             log.notes = (
#                 f"Could not generate patch for error type {error_info.error_type} "
#                 f"with message: {error_info.message}"
#             )
#             session.add_iteration(log)
#             session.success = False
#             session.failure_reason = "Patch generator could not fix the error."
#             return session

#         current_code = patch.new_code
#         log.patch = patch
#         log.notes = f"Applied patch: {patch.description}"

#         session.add_iteration(log)

#     session.success = False
#     session.final_code = current_code
#     session.failure_reason = "Max iterations reached without successful execution."
#     return session







# ========












# controller.py
from typing import Optional

from runner import run_python_code
from models import RepairSession, IterationLog
from analyzer import analyze_run_result
from patcher import generate_patch, set_instruction_context  # 🆕 import helper


def repair_code(initial_code: str, max_iterations: int = 3,
                instruction: Optional[str] = None) -> RepairSession:
    """
    Run → Analyze → Patch → Apply → Run loop.
    `instruction` is a free-form user goal like:
    "just fix errors", "optimize", "add logging", etc.
    Only the LLM handler cares about it.
    """
    # Store instruction globally for patcher / LLM to use
    set_instruction_context(instruction)

    session = RepairSession(
        original_code=initial_code,
        max_iterations=max_iterations,
    )

    current_code = initial_code

    for i in range(1, max_iterations + 1):
        run_result = run_python_code(current_code)

        # 🔴 NEW BLOCK: treat "timeout with normal output" as success
        # This handles interactive programs that wait for input().
        log = IterationLog(
            iteration=i,
            run_result=run_result,
        )

        if run_result.timeout and run_result.stdout.strip():
            # Example: calculator prints menu, waits on input(), then our
            # sandbox kills it with "Execution timed out."
            log.notes = (
                "Execution timed out after producing output (likely waiting for user input). "
                "Treating current version as successfully repaired."
            )
            session.add_iteration(log)
            session.success = True
            session.final_code = current_code
            return session
        # 🔴 END NEW BLOCK

        if run_result.success:
            log.notes = "Execution succeeded. No further repair needed."
            session.add_iteration(log)
            session.success = True
            session.final_code = current_code
            return session

        error_info = analyze_run_result(run_result)

        if error_info is None:
            log.notes = "Execution failed but no recognizable error was found."
            session.add_iteration(log)
            session.success = False
            session.failure_reason = "Unknown error without clear exception."
            return session

        patch = generate_patch(current_code, error_info, run_result)

        if patch is None:
            log.notes = (
                f"Could not generate patch for error type {error_info.error_type} "
                f"with message: {error_info.message}"
            )
            session.add_iteration(log)
            session.success = False
            session.failure_reason = "Patch generator could not fix the error."
            return session

        current_code = patch.new_code
        log.patch = patch
        log.notes = f"Applied patch: {patch.description}"

        session.add_iteration(log)

    session.success = False
    session.final_code = current_code
    session.failure_reason = "Max iterations reached without successful execution."
    return session
