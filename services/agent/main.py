"""
P vs NP Agent Microservice

This service orchestrates the decomposition of the P vs NP problem into tractable sub-questions,
creates Git issues using a Gitea API client, synthesizes community contributions, and dynamically
reprioritizes the backlog.

Core Endpoints:
- POST /decompose: Takes a high-level problem statement (e.g., "Is P = NP?") and calls an LLM to
  decompose it into subdomains/sub-questions.
- POST /create-tasks: Creates detailed micro-tasks from the decomposed subdomains, generating Git issues.
- POST /synthesize: Aggregates contributions (issues, PRs, comments) and runs a summarization via an LLM.
- POST /prioritize: Reprioritizes the current task backlog by evaluating engagement and contribution metrics.
  
External integrations:
- LLM Backend: Called via REST API (e.g., GPT-4)
- Gitea API Client: Used to create and manage Git issues/Pull Requests.
- Database/Cache: PostgreSQL and Redis reused from the common platform.
"""

import os
import requests
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="P vs NP Agent Service", version="0.1.0")

# Environment variables for external API endpoints / keys
LLM_API_URL = os.getenv("LLM_API_URL", "http://llm-backend:8000/decompose")
GITEA_API_URL = os.getenv("GITEA_API_URL", "http://gitea:3000/api/v1")
GITEA_TOKEN = os.getenv("GITEA_TOKEN", "replace-with-your-token")

# Request/response Models
class DecompositionRequest(BaseModel):
    problem_statement: str = Field(..., description="High-level problem statement (e.g., 'Is P = NP?')")
    formal_definitions: Optional[str] = Field(None, description="Any formal definitions or known reductions.")

class DecompositionResponse(BaseModel):
    subdomains: List[str] = Field(..., description="A list of key subdomains and barriers to resolve.")

class Task(BaseModel):
    title: str
    description: str
    labels: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)

class SynthesisRequest(BaseModel):
    contributions: List[str] = Field(..., description="List of text inputs from merged PRs/comments.")

class SynthesisResponse(BaseModel):
    summary: str

class PrioritizationRequest(BaseModel):
    task_ids: List[int] = Field(..., description="List of task IDs to reprioritize.")

class PrioritizationResponse(BaseModel):
    prioritized_tasks: List[int]

# Sample Endpoint: Decompose
@app.post("/decompose", response_model=DecompositionResponse)
def decompose_problem(req: DecompositionRequest):
    """
    Decomposes the provided problem statement into its core subdomains/barriers using an LLM.
    """
    try:
        # Call the LLM backend with the problem statement and any formal definitions.
        payload = {
            "prompt": f"Decompose the problem: {req.problem_statement}\nFormal details: {req.formal_definitions or 'None'}\nList the top 10 sub-questions."
        }
        response = requests.post(LLM_API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        subdomains = data.get("subdomains", [])
        return DecompositionResponse(subdomains=subdomains)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Sample Endpoint: Create Tasks (Issues)
@app.post("/create-tasks", response_model=List[Task])
def create_tasks(subdomains: List[str] = Body(..., embed=True, description="List of subdomains returned by /decompose")):
    """
    Creates micro-tasks (Git issues) for each subdomain by filling in issue templates.
    Uses the Gitea API to create issues on the repository.
    """
    tasks = []
    for index, sub in enumerate(subdomains, start=1):
        task = Task(
            title=f"Issue #{index}: Explore {sub}",
            description=f"Please research and compile literature and potential proof techniques regarding '{sub}'.\n\nSee attached template for detailed instructions.",
            labels=["decomposition", "research", "P vs NP"],
            assignees=[]
        )
        # Here you could call a helper function create_gitea_issue(task) to interact with Gitea's API.
        # For demonstration, we append the task directly.
        tasks.append(task)
    return tasks

# Sample Endpoint: Synthesize Contributions
@app.post("/synthesize", response_model=SynthesisResponse)
def synthesize_contributions(req: SynthesisRequest):
    """
    Aggregates contributions (from issues, PRs, etc.) and summarizes them using an LLM summarization prompt.
    """
    try:
        # Concatenate all contributions and send to the LLM API for summarization.
        combined_text = "\n".join(req.contributions)
        payload = {
            "prompt": f"Summarize the following contributions to the P vs NP research:\n{combined_text}"
        }
        response = requests.post(LLM_API_URL + "/synthesize", json=payload)
        response.raise_for_status()
        data = response.json()
        summary = data.get("summary", "No summary available.")
        return SynthesisResponse(summary=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Sample Endpoint: Prioritize Tasks
@app.post("/prioritize", response_model=PrioritizationResponse)
def prioritize_tasks(req: PrioritizationRequest):
    """
    Reprioritizes tasks based on engagement metrics from the community.
    This is a placeholder that simply returns the sorted task IDs.
    """
    # In a real implementation, this would query engagement metrics from the database,
    # weigh each task's value, and re-sort the backlog accordingly.
    prioritized = sorted(req.task_ids)
    return PrioritizationResponse(prioritized_tasks=prioritized)

# Health Check
@app.get("/health")
def health():
    return {"status": "P vs NP Agent is live"}