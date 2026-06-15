# cm1_test_mcp

Test MCP server for **CM1** experiment job management — the CM1 counterpart of
`demo_tools_mcp`. Lets the closed-loop agents run end to end without a real
~2-hour CM1 run; swap the URL back to production later with no code change.

## Tools (same spec as production)

| Tool | Purpose |
|---|---|
| `job_submit(payload)` | Queue an experiment batch → `{job_id, workspace_name}` |
| `job_status(job_id)` | `running` until `_JOB_DELAY` elapses, then `completed` |
| `job_plot(job_id, ...)` | Return the CM1 figure URLs (+ report) |
| `jobs_list(filter)` | List submitted jobs |

## Add your figures

Upload the PNGs (e.g. to postimg) and paste their direct image URLs into
`_FIGURE_URLS` at the top of `server.py`. Optionally set `_REPORT_URL`.

## Deploy

```bash
# FastMCP Cloud
fastmcp deploy server.py:mcp --name cm1-job-management

# or run locally
fastmcp run server.py:mcp
```

## Wire the agent to it

```bash
export CM1_MCP_URL=<deployed server url>
export CM1_MCP_API_KEY=<key>
export CM1_MCP_AUTH=bearer        # FastMCP Cloud uses bearer; x-api-key otherwise
```

`job_submit`, `job_status`, and `job_plot` all hit this one URL.
