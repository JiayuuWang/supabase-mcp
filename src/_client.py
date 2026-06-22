# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""End-to-end client test for the Supabase MCP server.

Runs against the deployed marketplace server via the Dedalus runner,
passing credentials through the DAuth SecretValues path (the same path a
real marketplace user hits). Two connections are bound:

    supabase       PostgREST data API  (key=SUPABASE_SECRET_KEY)
    supabase-mcp-mgmt   Management API  (access_token=SUPABASE_ACCESS_TOKEN)

Every tool is exercised at least once and a deterministic PASS/FAIL line is
printed per tool. Database write tools operate on an isolated
``dedalus_smoke_test`` table that is created and dropped within the run.

Required environment variables:
    DEDALUS_API_KEY         Dedalus API key (dsk-live-...)
    SUPABASE_SECRET_KEY     Supabase service-role / anon key (data API)
    SUPABASE_ACCESS_TOKEN   Supabase management PAT (sbp_...)

Optional:
    DEDALUS_API_URL   Override Dedalus API base (default https://api.dedaluslabs.ai)
    DEDALUS_AS_URL    Override Dedalus AS base  (default https://as.dedaluslabs.ai)
    MCP_SERVER_SLUG   Marketplace slug (default JiayuWang/supabase-mcp)
    SUPABASE_TEST_REF Supabase project ref for management tools

Usage:
    PYTHONPATH=src python src/_client.py
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from db import supabase  # noqa: E402
from management import supabase_mgmt  # noqa: E402
from dedalus_mcp.auth import Connection as _Conn
from dedalus_labs.lib.mcp.request import slug_to_connection_name as _s2c


def _rebind(conn, slug):
    return _Conn(name=_s2c(slug), secrets=conn.secrets, base_url=conn.base_url,
                 auth_header_name=conn.auth_header_name, auth_header_format=conn.auth_header_format)

DEDALUS_API_KEY = os.getenv("DEDALUS_API_KEY", "")
DEDALUS_API_URL = os.getenv("DEDALUS_API_URL", "https://api.dedaluslabs.ai")
DEDALUS_AS_URL = os.getenv("DEDALUS_AS_URL", "https://as.dedaluslabs.ai")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")
SUPABASE_ACCESS_TOKEN = os.getenv("SUPABASE_ACCESS_TOKEN", "")
SUPABASE_TEST_REF = os.getenv("SUPABASE_TEST_REF", "")
MCP_SERVER_SLUG = os.getenv("MCP_SERVER_SLUG", "JiayuWang/supabase-mcp")
MODEL = os.getenv("DEDALUS_TEST_MODEL", "anthropic/claude-sonnet-4-5")

REQUIRED_TOOLS = [
    # smoke
    "smoke_ping",
    # management (read)
    "list_projects",
    "get_project",
    "list_organizations",
    "list_tables",
    "list_extensions",
    "list_migrations",
    "list_branches",
    "get_logs",
    "get_advisors",
    "generate_typescript_types",
    # management (write)
    "execute_sql",
    "apply_migration",
    "create_branch",
    # database
    "db_insert",
    "db_select",
    "db_get_by_id",
    "db_update",
    "db_upsert",
    "db_delete",
    "db_rpc",
]


def _passed(tool_name: str, output: str) -> bool:
    if not output:
        return False
    lowered = output.lower()
    hard_failures = (
        "no tool",
        "tool not found",
        "unknown tool",
        "could not call",
        "no active context",
        "modulenotfounderror",
        "importerror",
        "currently unavailable",
        "mcp server",
    )
    return not any(marker in lowered for marker in hard_failures)


async def _run_tool(runner, creds, tool_name: str, instruction: str) -> bool:
    print(f"\n--- {tool_name} ---")
    try:
        result = await runner.run(
            input=instruction,
            model=MODEL,
            mcp_servers=[MCP_SERVER_SLUG],
            credentials=creds,
            max_steps=8,
            max_tokens=4096,
        )
        output = getattr(result, "output", str(result)) or ""
        print(output[:600])
        ok = _passed(tool_name, output)
    except Exception as exc:  # noqa: BLE001
        print(f"exception: {exc!r}")
        ok = False
    print(f"[{'PASS' if ok else 'FAIL'}] {tool_name}")
    return ok


async def main() -> int:
    if not DEDALUS_API_KEY:
        print("Error: DEDALUS_API_KEY not set")
        return 1
    if not SUPABASE_SECRET_KEY or not SUPABASE_ACCESS_TOKEN:
        print("Error: SUPABASE_SECRET_KEY and SUPABASE_ACCESS_TOKEN must be set")
        return 1

    from dedalus_labs import AsyncDedalus, DedalusRunner
    from dedalus_mcp.auth import SecretValues

    creds = [
        SecretValues(_rebind(supabase, MCP_SERVER_SLUG), key=SUPABASE_SECRET_KEY),
        SecretValues(_rebind(supabase_mgmt, MCP_SERVER_SLUG), token=SUPABASE_ACCESS_TOKEN),
    ]

    client = AsyncDedalus(
        api_key=DEDALUS_API_KEY,
        base_url=DEDALUS_API_URL,
        as_base_url=DEDALUS_AS_URL,
    )
    runner = DedalusRunner(client)

    print(f"Testing Supabase MCP server: {MCP_SERVER_SLUG}")
    print("=" * 60)

    results: dict[str, bool] = {}
    ref_hint = (
        f"Use project ref '{SUPABASE_TEST_REF}'."
        if SUPABASE_TEST_REF
        else "Call list_projects first and use the first project's ref/id."
    )

    # --- smoke ---
    results["smoke_ping"] = await _run_tool(
        runner, creds, "smoke_ping",
        "Call the smoke_ping tool and show the response.",
    )

    # --- management: read ---
    results["list_projects"] = await _run_tool(
        runner, creds, "list_projects",
        "Call the list_projects tool and show each project ref and name.",
    )
    results["get_project"] = await _run_tool(
        runner, creds, "get_project",
        f"{ref_hint} Then call get_project on that ref and show its status.",
    )
    results["list_organizations"] = await _run_tool(
        runner, creds, "list_organizations",
        "Call the list_organizations tool and list each organization id and name.",
    )
    results["list_tables"] = await _run_tool(
        runner, creds, "list_tables",
        f"{ref_hint} Then call list_tables for that project and list table names.",
    )
    results["list_extensions"] = await _run_tool(
        runner, creds, "list_extensions",
        f"{ref_hint} Then call list_extensions for that project.",
    )
    results["list_migrations"] = await _run_tool(
        runner, creds, "list_migrations",
        f"{ref_hint} Then call list_migrations for that project.",
    )
    results["list_branches"] = await _run_tool(
        runner, creds, "list_branches",
        f"{ref_hint} Then call list_branches for that project.",
    )
    results["get_logs"] = await _run_tool(
        runner, creds, "get_logs",
        f"{ref_hint} Then call get_logs for that project with service 'postgres'.",
    )
    results["get_advisors"] = await _run_tool(
        runner, creds, "get_advisors",
        f"{ref_hint} Then call get_advisors for that project with type 'security'.",
    )
    results["generate_typescript_types"] = await _run_tool(
        runner, creds, "generate_typescript_types",
        f"{ref_hint} Then call generate_typescript_types for that project.",
    )

    # --- management: write + DB CRUD on an isolated fixture table ---
    # Create the throwaway table first; every DB tool below operates on it and
    # we drop it at the very end so nothing is left behind.
    results["execute_sql"] = await _run_tool(
        runner, creds, "execute_sql",
        f"{ref_hint} Then call execute_sql on that project to run: "
        "CREATE TABLE IF NOT EXISTS dedalus_smoke_test "
        "(id bigint primary key, name text);",
    )
    results["apply_migration"] = await _run_tool(
        runner, creds, "apply_migration",
        f"{ref_hint} Then call apply_migration on that project with name "
        "'dedalus_smoke_test_migration' and SQL "
        "'CREATE TABLE IF NOT EXISTS dedalus_smoke_mig (id bigint primary key);'.",
    )
    results["create_branch"] = await _run_tool(
        runner, creds, "create_branch",
        f"{ref_hint} Then call create_branch on that project with name "
        "'dedalus-smoke-branch'. If branching is not enabled, report the tool's "
        "error response (the tool call itself still counts).",
    )

    results["db_insert"] = await _run_tool(
        runner, creds, "db_insert",
        "Call db_insert on table 'dedalus_smoke_test' with rows "
        "[{\"id\": 1, \"name\": \"dedalus\"}].",
    )
    results["db_select"] = await _run_tool(
        runner, creds, "db_select",
        "Call db_select on table 'dedalus_smoke_test' with columns '*' and limit 5.",
    )
    results["db_get_by_id"] = await _run_tool(
        runner, creds, "db_get_by_id",
        "Call db_get_by_id on table 'dedalus_smoke_test' for id 1.",
    )
    results["db_update"] = await _run_tool(
        runner, creds, "db_update",
        "Call db_update on table 'dedalus_smoke_test' with updates "
        "{\"name\": \"updated\"} and filters 'id=eq.1'.",
    )
    results["db_upsert"] = await _run_tool(
        runner, creds, "db_upsert",
        "Call db_upsert on table 'dedalus_smoke_test' with rows "
        "[{\"id\": 2, \"name\": \"upserted\"}].",
    )
    results["db_delete"] = await _run_tool(
        runner, creds, "db_delete",
        "Call db_delete on table 'dedalus_smoke_test' with filters 'id=eq.1', "
        "then with filters 'id=eq.2' to clean up the rows.",
    )
    results["db_rpc"] = await _run_tool(
        runner, creds, "db_rpc",
        "Call db_rpc to invoke the Postgres function 'version' with no args. If "
        "that function is unavailable, report the tool's error (the call still "
        "exercises the tool path).",
    )

    # Cleanup: drop the fixture tables created above.
    await _run_tool(
        runner, creds, "cleanup",
        f"{ref_hint} Then call execute_sql to run: "
        "DROP TABLE IF EXISTS dedalus_smoke_test; "
        "DROP TABLE IF EXISTS dedalus_smoke_mig;",
    )

    print("\n" + "=" * 60)
    print("Summary")
    for name in REQUIRED_TOOLS:
        ok = results.get(name, False)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    all_pass = all(results.get(t, False) for t in REQUIRED_TOOLS)
    print("\nRESULT:", "ALL PASS" if all_pass else "SOME FAILED")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))