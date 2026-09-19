# WHOOP MCP — personal WHOOP data for any agent harness

Local MCP (stdio) server exposing your WHOOP data (recovery, sleep, strain,
workouts, profile) to agent harnesses: **Hermes, Claude Desktop, Claude Code**,
and anything that speaks MCP. Client secret lives in the **Windows keychain**;
OAuth tokens auto-refresh.

## One-time setup

1. **Register the app** at https://app.developer.whoop.com → Create New App:
   - Name: `personal-whoop-agent`
   - Contacts: your email
   - **Privacy policy URL:** must be a real HTTPS URL (a `localhost` URL is
     **silently rejected with HTTP 422**). Host the file below (e.g. GitHub
     Pages / a gist's raw HTML page) once, or any URL you control.
   - Redirect URL: `http://localhost:49152/callback`
   - Scopes: `read:profile`, `read:body_measurement`, `read:cycles`,
     `read:recovery`, `read:sleep`, `read:workout` (the `offline` scope is
     requested at OAuth time, not configured in the dashboard)
2. **Store credentials** (keychain service `whoop-dev-app`), from this dir:
   ```bash
   python -m whoop_mcp --store        # prompts for client id / secret / redirect
   ```
3. **Authorize:**
   ```bash
   python -m whoop_mcp                # opens browser, listens for callback
   ```

## Hermes setup

`hermes config set mcp_servers.whoop.command python` then, via config.yaml
under `mcp_servers:`, add:

```yaml
mcp_servers:
  whoop:
    command: "C:/Users/gaura/Documents/Projects/whoop-app/.venv/Scripts/python.exe"
    args: ["-m", "whoop_mcp.server"]
    env:
      PYTHONPATH: "C:/Users/gaura/Documents/Projects/whoop-app"
    timeout: 120
```

Restart Hermes → tools appear as `mcp_whoop_*`.

## Claude Desktop / Claude Code

claude_desktop_config.json:

```json
{
  "mcpServers": {
    "whoop": {
      "command": "C:/Users/gaura/Documents/Projects/whoop-app/.venv/Scripts/python.exe",
      "args": ["-m", "whoop_mcp.server"],
      "env": {"PYTHONPATH": "C:/Users/gaura/Documents/Projects/whoop-app"}
    }
  }
}
```

Claude Code: `claude mcp add whoop -- C:/Users/gaura/Documents/Projects/whoop-app/.venv/Scripts/python.exe -m whoop_mcp.server`

## ChatGPT / anything else

Any harness that can run `python` can use the raw REST path tokens in the
keychain — or call these same tools via any stdio MCP client.

## Tools

- `whoop_auth_status` — token state
- `whoop_authorization_url` / `whoop_complete_authorization` — in-chat re-auth
- `whoop_profile`, `whoop_body_measurements`
- `whoop_cycles`, `whoop_cycle_by_id`, `whoop_recoveries`
- `whoop_sleeps`, `whoop_sleep_by_id`, `whoop_workouts`, `whoop_workout_by_id`
- `whoop_daily_summary` — last-N-days merged Strain/Recovery/Sleep table

## Privacy policy

A `privacy-policy.md` is included — host it (GitHub Pages, gist, or your site)
and paste the URL into the WHOOP dashboard.
