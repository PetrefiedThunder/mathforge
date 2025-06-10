"""
This module provides a gamification service for crowdsourcing incremental math problems.
It allows users to submit problems (theorem edges) and propose next steps to break down theorems
into their most basic components.

Endpoints:
- POST /submit: Submit a new problem edge with an optional proposed next step.
- POST /propose/{problem_id}: Propose an additional next step for an existing problem.
- GET /problems: List all submitted problems with their proposed steps.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

app = FastAPI(title="Math Gamification Service")

# In-memory storage for demonstration. In a production app, use a database.
PROBLEMS = {}

class ProblemSubmission(BaseModel):
    theorem: str = Field(..., description="The statement of the theorem to break down.")
    current_edge: str = Field(..., description="The current edge or state of the theorem.")
    next_step: Optional[str] = Field(
        None, description="An optional proposed next step to progress from the current edge."
    )

class ProblemResponse(BaseModel):
    id: str
    theorem: str
    current_edge: str
    proposed_steps: List[str] = Field(default_factory=list, description="List of proposed next steps.")

@app.post("/submit", response_model=ProblemResponse)
def submit_problem(problem: ProblemSubmission):
    """
    Submit a new problem for crowdsourcing.
    A unique ID is generated for the problem, allowing multiple users to propose steps.
    """
    problem_id = str(uuid.uuid4())
    PROBLEMS[problem_id] = {
        "theorem": problem.theorem,
        "current_edge": problem.current_edge,
        "proposed_steps": [problem.next_step] if problem.next_step else []
    }
    return ProblemResponse(
        id=problem_id,
        theorem=problem.theorem,
        current_edge=problem.current_edge,
        proposed_steps=PROBLEMS[problem_id]["proposed_steps"],
    )

@app.post("/propose/{problem_id}", response_model=ProblemResponse)
def propose_next_step(problem_id: str, next_step: str):
    """
    Propose an additional next step for an existing problem.
    This crowdsources further breakdown steps from the community.
    """
    if problem_id not in PROBLEMS:
        raise HTTPException(status_code=404, detail="Problem not found")
    PROBLEMS[problem_id]["proposed_steps"].append(next_step)
    data = PROBLEMS[problem_id]
    return ProblemResponse(
        id=problem_id,
        theorem=data["theorem"],
        current_edge=data["current_edge"],
        proposed_steps=data["proposed_steps"],
    )

@app.get("/problems", response_model=List[ProblemResponse])
def list_problems():
    """
    List all submitted problems with their proposed next steps.
    Great for browsing current crowdsourced ideas.
    """
    return [
        ProblemResponse(
            id=pid,
            theorem=data["theorem"],
            current_edge=data["current_edge"],
            proposed_steps=data["proposed_steps"],
        )
        for pid, data in PROBLEMS.items()
    ]