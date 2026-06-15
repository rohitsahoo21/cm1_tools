"""Test MCP server for CM1 experiment job management.

Mirrors the production CM1 Temporal job-management server so the closed-loop
agents can run end to end WITHOUT a real ~2-hour CM1 run:
- Stage 4 calls job_submit to queue an experiment batch.
- Stage 5 (Experiment Analysis Agent) calls job_status to poll progress and
  job_plot to fetch the result figures.

Same tool spec as production — point the agent's CM1_MCP_URL at this server,
demo the loop, then swap the URL back to production with no code change.

Deploy (FastMCP Cloud):  fastmcp deploy server.py:mcp --name cm1-job-management
Run locally:             fastmcp run server.py:mcp

To use your own figures: upload the PNGs (e.g. to postimg) and paste their
direct image URLs into _FIGURE_URLS below.
"""

import json
import time
import uuid

from fastmcp import FastMCP

mcp = FastMCP("cm1-job-management")

# In-memory job store (resets on server restart).
_JOBS: dict[str, dict] = {}

# Seconds a job "runs" before job_status flips to completed (0 = instant).
_JOB_DELAY = 0

# CM1 result assets returned by job_plot. Paste your hosted PNG URLs here.
_REPORT_URL = ""
_FIGURE_URLS = [
    "https://i.postimg.cc/L5ztYZLS/energy-budget-comparison.png",
    "https://i.postimg.cc/MHy7MjVH/intensity-anomalies.png",
    "https://i.postimg.cc/3NgX4Dmd/intensity-comparison.png",
    "https://i.postimg.cc/HnQwc7Xr/moisture-budget-comparison.png",
    "https://i.postimg.cc/rsS10txz/phase-timing-summary.png",
    "https://i.postimg.cc/BbxTL1HT/rain-train-comparison.png",
    "https://i.postimg.cc/brQxD2k9/stability-cape-cin-anomalies.png",
    "https://i.postimg.cc/3NgX4DmC/stability-cape-cin-comparison.png",
    "https://i.postimg.cc/2y4QbBhx/structure-anomalies.png",
    "https://i.postimg.cc/KcLrsCVV/structure-comparison.png",
    "https://i.postimg.cc/y69Xr25t/vorticity-levels-comparison.png",
]


@mcp.tool()
def job_submit(payload: dict) -> str:
    """Submit a CM1 experiment batch; returns job_id and workspace_name."""
    job_id = str(uuid.uuid4())[:8]
    workspace = (
        payload.get("workspace_name")
        or payload.get("output", {}).get("dir", "")
        or f"cm1_ws_{job_id}"
    )
    _JOBS[job_id] = {
        "job_id": job_id,
        "started_at": time.time(),
        "workspace_name": workspace,
        "payload": payload,
    }
    return json.dumps({
        "job_id": job_id,
        "workspace_name": workspace,
        "config_received": payload,
    })


@mcp.tool()
def job_status(job_id: str) -> str:
    """Return 'running' until _JOB_DELAY seconds elapse, then 'completed'."""
    job = _JOBS.get(job_id)
    if not job:
        return json.dumps({
            "job_id": job_id,
            "status": "completed",
            "workspace_name": f"cm1_ws_{job_id}",
        })
    elapsed = time.time() - job.get("started_at", 0)
    status = "completed" if elapsed >= _JOB_DELAY else "running"
    return json.dumps({
        "job_id": job_id,
        "status": status,
        "workspace_name": job.get("workspace_name", ""),
    })


@mcp.tool()
def job_plot(job_id: str, workspace_name: str = "", user_name: str = "") -> str:
    """Get the CM1 figure URLs (and report) for a completed job.

    Args:
        job_id: The job to fetch plots for.
        workspace_name: Workspace name (production uses it to locate outputs).
        user_name: User name (production uses it for auth/routing).

    In production this reads the experiment output directory / object storage.
    For this test server it returns the URLs in _FIGURE_URLS.
    """
    return json.dumps({
        "job_id": job_id,
        "report_url": _REPORT_URL,
        "figures": _FIGURE_URLS,
    })


@mcp.tool()
def jobs_list(filter: str = "all") -> str:
    """List submitted jobs with id, status, and workspace_name."""
    jobs = []
    for j in _JOBS.values():
        elapsed = time.time() - j.get("started_at", 0)
        jobs.append({
            "job_id": j["job_id"],
            "status": "completed" if elapsed >= _JOB_DELAY else "running",
            "workspace_name": j.get("workspace_name", ""),
        })
    return json.dumps({"jobs": jobs})


if __name__ == "__main__":
    mcp.run()
