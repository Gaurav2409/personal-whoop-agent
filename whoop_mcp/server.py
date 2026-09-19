"""WHOOP MCP server (stdio). Tools are agent-friendly: JSON in / JSON out,
auto-refreshing auth, clear AuthNeededError guidance when not authorized."""
import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import client, config
from .auth import AuthNeededError, token_status

mcp = FastMCP("whoop")

SCOPE_OF = {
    "profile": "read:profile",
    "body_measurements": "read:body_measurement",
    "cycles": "read:cycles",
    "recoveries": "read:recovery",
    "sleeps": "read:sleep",
    "workouts": "read:workout",
}


def _guard(fn, *a, **kw) -> str:
    try:
        return json.dumps(fn(*a, **kw), default=str)
    except AuthNeededError as e:
        return json.dumps({"error": "auth_needed", "message": str(e)})


@mcp.tool()
def whoop_auth_status() -> str:
    """Check whether WHOOP OAuth tokens are stored and valid."""
    return json.dumps(token_status())


@mcp.tool()
def whoop_authorization_url() -> str:
    """Build (and open) the WHOOP OAuth consent URL. Returns the URL to visit
    if the browser didn't open."""
    from .auth import build_authorize_url, open_browser_authorize
    try:
        url, _ = open_browser_authorize()
        return json.dumps({"authorization_url": url,
                           "note": "After granting, run `python -m whoop_mcp.auth` (listener) OR paste the redirect URL to whoop_complete_authorization."})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def whoop_complete_authorization(redirected_url: str) -> str:
    """Complete OAuth by pasting the full localhost redirect URL the browser
    landed on after granting consent (used when the local listener isn't running)."""
    from .auth import handle_callback
    return _guard(handle_callback, redirected_url)


@mcp.tool()
def whoop_profile() -> str:
    """Basic profile: user_id, name, email."""
    return _guard(client._get, "/user/profile/basic")


@mcp.tool()
def whoop_body_measurements() -> str:
    """Height, weight, max heart rate."""
    return _guard(client._get, "/user/measurement/body")


@mcp.tool()
def whoop_cycles(limit: int = 10, max_pages: int = 5) -> str:
    """Physiological cycles (day strain, avg/max HR), newest first. Paginates 25/page."""
    return _guard(client.paginate, "/cycle", {"limit": min(limit, 25)}, max_pages)


@mcp.tool()
def whoop_collection(scope: str, limit: int = 25, start: str = "", end: str = "", max_pages: int = 20) -> str:
    """Generic paginated collection fetch with date filters (ISO 8601).
    scope: one of "cycles", "recoveries", "sleeps", "workouts".
    start: only items at/after this ISO time; end: items before this ISO time."""
    paths = {"cycles": "/cycle", "recoveries": "/recovery",
             "sleeps": "/activity/sleep", "workouts": "/activity/workout"}
    params = {"limit": min(limit, 25)}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    return _guard(client.paginate, paths[scope], params, max_pages)


@mcp.tool()
def whoop_cycle_by_id(cycle_id: int) -> str:
    """One cycle by numeric ID."""
    return _guard(client._get, f"/cycle/{cycle_id}")


@mcp.tool()
def whoop_cycle_recoveries(limit: int = 10, start: str = "", end: str = "", max_pages: int = 20) -> str:
    """Recovery scores (HRV, RHR, SpO2, skin temp), newest first."""
    params = {"limit": min(limit, 25)}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    return _guard(client.paginate, "/recovery", params, max_pages)


@mcp.tool()
def whoop_recoveries_for_cycle(cycle_id: int) -> str:
    """Recovery record attached to a specific cycle (numeric ID)."""
    return _guard(client._get, f"/cycle/{cycle_id}/recovery")


@mcp.tool()
def whoop_sleep_for_cycle(cycle_id: int) -> str:
    """Sleep record attached to a specific cycle (numeric ID)."""
    return _guard(client._get, f"/cycle/{cycle_id}/sleep")


@mcp.tool()
def whoop_sleeps(limit: int = 10, max_pages: int = 5) -> str:
    """Sleep records: performance, consistency, stage breakdown (REM/deep/light/awake), respiratory rate."""
    return _guard(client.paginate, "/activity/sleep", {"limit": min(limit, 25)}, max_pages)


@mcp.tool()
def whoop_sleep_by_id(sleep_id: str) -> str:
    """One sleep record by UUID."""
    return _guard(client._get, f"/sleep/{sleep_id}")


@mcp.tool()
def whoop_workouts(limit: int = 10, start: str = "", end: str = "", max_pages: int = 5) -> str:
    """Workouts: sport, strain, HR, kilojoules, distance, zone durations."""
    params = {"limit": min(limit, 25)}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    return _guard(client.paginate, "/activity/workout", params, max_pages)


@mcp.tool()
def whoop_workout_by_id(workout_id: str) -> str:
    """One workout by UUID."""
    return _guard(client._get, f"/activity/workout/{workout_id}")


@mcp.tool()
def whoop_daily_summary(days: int = 1) -> str:
    """Compact per-day summary for the last N days: strain, recovery, sleep
    performance, sleep hours — merged from cycles + recovery + sleep collections."""
    import time as _t
    from datetime import datetime, timezone

    def _summary() -> Any:
        start = datetime.fromtimestamp(_t.time() - days * 86400, timezone.utc).isoformat()
        cycles = client.paginate("/cycle", {"limit": 25, "start": start}, 3)
        recs = client.paginate("/recovery", {"limit": 25, "start": start}, 3)
        sleeps = client.paginate("/activity/sleep", {"limit": 25, "start": start}, 3)

        def day_of(iso):
            return (iso or "")[:10]

        by_day: dict[str, dict] = {}
        for c in cycles["records"]:
            s = c.get("score") or {}
            by_day.setdefault(day_of(c.get("start")), {})["strain"] = s.get("strain")
        for r in recs["records"]:
            s = r.get("score") or {}
            d = by_day.setdefault(day_of(r.get("created_at")), {})
            d["recovery_pct"] = s.get("recovery_score")
            d["resting_hr"] = s.get("resting_heart_rate")
            d["hrv_ms"] = s.get("hrv_rmssd_milli")
            d["spo2_pct"] = s.get("spo2_percentage")
        for sl in sleeps["records"]:
            s = sl.get("score") or {}
            d = by_day.setdefault(day_of(sl.get("start")), {})
            d["sleep_performance_pct"] = s.get("sleep_performance_percentage")
            stages = (s.get("stage_summary") or {})
            d["sleep_hours"] = round(
                ((stages.get("total_light_sleep_time_milli", 0)
                  + stages.get("total_slow_wave_sleep_time_milli", 0)
                  + stages.get("total_rem_sleep_time_milli", 0)) / 3_600_000), 2)
        return {"days": days, "summary": by_day}

    return _guard(_summary)


@mcp.tool()
def whoop_coaching_brief(days: int = 30) -> str:
    """Structured evidence brief for a health coach: per-day merged data, plus
    trend statistics (recovery/HRV/RHR/sleep/strain means and deltas) and
    training-load context for the last N days. This is the primary tool for
    coaching conversations; pair with the peak-human doctrine corpus at
    C:/Users/gaura/Documents/Projects/whoop-app/reference/peakhuman."""
    import time as _t
    import statistics as _stat
    from datetime import datetime, timezone

    def _brief():
        start = datetime.fromtimestamp(_t.time() - days * 86400, timezone.utc).isoformat()
        cycles = client.paginate("/cycle", {"limit": 25, "start": start}, 8)
        recs = client.paginate("/recovery", {"limit": 25, "start": start}, 8)
        sleeps = client.paginate("/activity/sleep", {"limit": 25, "start": start}, 8)
        workouts = client.paginate("/activity/workout", {"limit": 25, "start": start}, 4)

        rows: dict[str, dict] = {}
        for c in cycles["records"]:
            s = c.get("score") or {}
            rows.setdefault((c.get("start") or "")[:10], {})["strain"] = s.get("strain")
            rows[(c.get("start") or "")[:10]]["cycle_top_hr"] = s.get("max_heart_rate")
        for r in recs["records"]:
            s = r.get("score") or {}
            d = rows.setdefault((r.get("created_at") or "")[:10], {})
            d.update(recovery=s.get("recovery_score"), rhr=s.get("resting_heart_rate"),
                     hrv=s.get("hrv_rmssd_milli"), spo2=s.get("spo2_percentage"))
        for sl in sleeps["records"]:
            s = sl.get("score") or {}
            d = rows.setdefault((sl.get("start") or "")[:10], {})
            d.update(sleep_perf=s.get("sleep_performance_percentage"),
                     sleep_consistency=s.get("sleep_consistency_percentage"))
            st = s.get("stage_summary") or {}
            d["sleep_hours"] = round(((st.get("total_light_sleep_time_milli", 0)
                + st.get("total_slow_wave_sleep_time_milli", 0)
                + st.get("total_rem_sleep_time_milli", 0)) / 3_600_000), 2)
        for w in workouts["records"]:
            s = w.get("score") or {}
            rows.setdefault((w.get("start") or "")[:10], {}) \
                .setdefault("workouts", []).append(
                {"sport": w.get("sport_name"), "strain": s.get("strain"),
                 "kj": round(s.get("kilojoule") or 0)})

        timeline = [{"date": k, **v} for k, v in sorted(rows.items())]

        def col(field):
            vals = [r[field] for r in timeline if r.get(field) is not None]
            return vals

        rec_vals, hrv_vals = col("recovery"), col("hrv")
        sleep_vals = col("sleep_perf")
        strain_vals = col("strain")

        def trend(vals):
            if not vals:
                return None
            half = max(1, len(vals) // 2)
            older, newer = vals[:half], vals[half:]
            return {
                "mean": round(_stat.mean(vals), 1),
                "recent_mean": round(_stat.mean(newer), 1) if newer else None,
                "delta_recent_vs_earlier": (round(_stat.mean(newer) - _stat.mean(older), 1)
                                            if newer and older else None),
                "n": len(vals),
            }

        week_rec = [r["recovery"] for r in timeline if r.get("recovery") is not None][-7:]
        return {
            "window_days": days,
            "trends": {"recovery": trend(rec_vals), "hrv": trend(hrv_vals),
                       "sleep_performance": trend(sleep_vals), "strain": trend(strain_vals)},
            "last_week_recovery": week_rec,
            "recovery_dips": [r for r in timeline if r.get("recovery") is not None and r["recovery"] < 40],
            "workout_count": sum(len(r.get("workouts") or []) for r in timeline),
            "timeline": timeline,
        }

    return _guard(_brief)


if __name__ == "__main__":
    mcp.run(transport="stdio")
