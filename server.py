"""Test MCP server for CM1 experiment job management.

Mirrors the production CM1 job-management server so the closed-loop agents run
end to end WITHOUT the HPC:
- Stage 4 calls job_submit to queue an experiment batch.
- Stage 5 (Experiment Analysis Agent) calls code_submit to ship the generated
  plot module, then job_status / job_plot to poll and fetch the figures.

This is a MOCK. It does NOT run the harness — there is no experiment data,
harness, or scientific-python env on the server. code_submit just *accepts*
the module (acknowledges receipt) and job_plot returns the preconfigured
_FIGURE_URLS. In production, code_submit would run cm1_harness.py on the HPC
where the data + harness live and job_plot would return the figures it made.

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

# In-memory stores (reset on restart).
_JOBS: dict[str, dict] = {}
_SUBMITTED: dict[str, int] = {}   # job_id -> length of code received (proof of receipt)

# Seconds a job "runs" before job_status flips to completed (0 = instant).
_JOB_DELAY = 0

# CM1 result figures returned by job_plot. Paste your hosted PNG URLs here —
# these should match the experiment/hypothesis being demoed.
_REPORT_URL = ""
_FIGURE_URLS = [
    "https://i.postimg.cc/fygQS4Rc/energy-budget-timeseries.png",
    "https://i.postimg.cc/1RWQjFrP/intensity-anomalies.png",
    "https://i.postimg.cc/c1DSb3BW/intensity-timeseries.png",
    "https://i.postimg.cc/L4ypbP3H/moisture-budget-timeseries.png",
    "https://i.postimg.cc/pV0H6jJM/phase-timing-comparison.png",
    "https://i.postimg.cc/Y2XHsFz0/structure-anomalies.png",
    "https://i.postimg.cc/Kc92HTD4/structure-timeseries.png",
    "https://i.postimg.cc/2jHDKW76/surface-flux-anomalies.png",
    "https://i.postimg.cc/ryhkP4NK/surface-flux-timeseries.png",
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
def code_submit(code: str, job_id: str = "default", input_dir: str = "") -> str:
    """Accept the generated plot module (MOCK — does not execute it).

    The real (HPC) endpoint would write the module and run cm1_harness.py on
    the experiment data. Here we just acknowledge receipt; job_plot returns the
    preconfigured _FIGURE_URLS. Reports figures_produced = len(_FIGURE_URLS) so
    the caller's "submitted, N figures" message matches what job_plot returns.
    """
    _SUBMITTED[job_id] = len(code or "")
    return json.dumps({
        "job_id": job_id,
        "status": "completed",
        "figures_produced": len(_FIGURE_URLS),
        "note": "mock — module accepted but not executed; figures are the preconfigured set",
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
    """Get the CM1 figure URLs (and report) for a job.

    MOCK: returns the preconfigured _FIGURE_URLS. In production this would
    return the figures the harness produced from the submitted module.
    """
    result = {"job_id": job_id, "figures": _FIGURE_URLS}
    if _REPORT_URL:
        result["report_url"] = _REPORT_URL
    return json.dumps(result)


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
