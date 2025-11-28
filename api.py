# # api.py
# from fastapi import FastAPI
# from pydantic import BaseModel
# from typing import List, Optional

# from controller import repair_code

# app = FastAPI(title="Local Code Repair API")


# class IterationLogDTO(BaseModel):
#     iteration: int
#     success: bool
#     timeout: bool
#     return_code: int
#     stdout: str
#     stderr: str
#     patch_description: Optional[str] = None
#     notes: str


# class RepairRequest(BaseModel):
#     code: str
#     max_iterations: int = 5


# class RepairResponse(BaseModel):
#     success: bool
#     final_code: Optional[str]
#     failure_reason: Optional[str]
#     iterations: List[IterationLogDTO]


# @app.post("/repair", response_model=RepairResponse)
# def repair_endpoint(req: RepairRequest):
#     session = repair_code(req.code, max_iterations=req.max_iterations)

#     iter_logs: List[IterationLogDTO] = []
#     for log in session.iterations:
#         iter_logs.append(
#             IterationLogDTO(
#                 iteration=log.iteration,
#                 success=log.run_result.success,
#                 timeout=log.run_result.timeout,
#                 return_code=log.run_result.return_code,
#                 stdout=log.run_result.stdout,
#                 stderr=log.run_result.stderr,
#                 patch_description=log.patch.description if log.patch else None,
#                 notes=log.notes,
#             )
#         )

#     return RepairResponse(
#         success=session.success,
#         final_code=session.final_code,
#         failure_reason=session.failure_reason,
#         iterations=iter_logs,
#     )




# api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from controller import repair_code  # we'll update signature in controller.py

app = FastAPI(title="Local Code Repair API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IterationLogDTO(BaseModel):
    iteration: int
    success: bool
    timeout: bool
    return_code: int
    stdout: str
    stderr: str
    patch_description: Optional[str] = None
    notes: str


class RepairRequest(BaseModel):
    code: str
    max_iterations: int = 5
    instruction: Optional[str] = None   # 🆕 user goal / request


class RepairResponse(BaseModel):
    success: bool
    final_code: Optional[str]
    failure_reason: Optional[str]
    iterations: List[IterationLogDTO]


@app.post("/repair", response_model=RepairResponse)
def repair_endpoint(req: RepairRequest):
    session = repair_code(
        req.code,
        max_iterations=req.max_iterations,
        instruction=req.instruction,   # 🆕 pass it down
    )

    iter_logs: List[IterationLogDTO] = []
    for log in session.iterations:
        iter_logs.append(
            IterationLogDTO(
                iteration=log.iteration,
                success=log.run_result.success,
                timeout=log.run_result.timeout,
                return_code=log.run_result.return_code,
                stdout=log.run_result.stdout,
                stderr=log.run_result.stderr,
                patch_description=log.patch.description if log.patch else None,
                notes=log.notes,
            )
        )

    return RepairResponse(
        success=session.success,
        final_code=session.final_code,
        failure_reason=session.failure_reason,
        iterations=iter_logs,
    )
