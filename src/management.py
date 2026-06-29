# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Supabase Management API tools (projects, orgs, branches, migrations, logs, advisors).

Uses SUPABASE_ACCESS_TOKEN (PAT) for authentication.
"""

from typing import Any

from pydantic import Field
from pydantic.dataclasses import dataclass

from dedalus_mcp import HttpMethod, HttpRequest, get_context, tool
from dedalus_mcp.auth import Connection, SecretKeys
from dedalus_mcp.types import ToolAnnotations

supabase_mgmt = Connection(
    name="JiayuWang(王嘉宇)-supabase-mcp-mgmt",
    secrets=SecretKeys(token="SUPABASE_ACCESS_TOKEN"),
    base_url="https://api.supabase.com/v1",
    auth_header_format="Bearer {api_key}",
)


@dataclass(frozen=True)
class MgmtResult:
    success: bool
    data: list[dict[str, Any]] | dict[str, Any] | None = Field(default_factory=None)
    error: str | None = None


def _handle_response(resp) -> MgmtResult:
    if resp.success:
        body = resp.response.body
        if isinstance(body, list):
            return MgmtResult(success=True, data=body)
        if isinstance(body, dict):
            return MgmtResult(success=True, data=body)
        return MgmtResult(success=True, data=body)
    return MgmtResult(success=False, error=resp.error.message if resp.error else "Request failed")


@tool(
    description="List all Supabase projects the user has access to",
    tags=["management", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_projects() -> MgmtResult:
    ctx = get_context()
    req = HttpRequest(method=HttpMethod.GET, path="/projects")
    return _handle_response(await ctx.dispatch(supabase_mgmt, req))


@tool(
    description="Get details of a specific Supabase project",
    tags=["management", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def get_project(ref: str) -> MgmtResult:
    ctx = get_context()
    req = HttpRequest(method=HttpMethod.GET, path=f"/projects/{ref}")
    return _handle_response(await ctx.dispatch(supabase_mgmt, req))


@tool(
    description="List all organizations the user belongs to",
    tags=["management", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_organizations() -> MgmtResult:
    ctx = get_context()
    req = HttpRequest(method=HttpMethod.GET, path="/organizations")
    return _handle_response(await ctx.dispatch(supabase_mgmt, req))


@tool(
    description="List database schemas in a project",
    tags=["schema", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_tables(ref: str) -> MgmtResult:
    ctx = get_context()
    req = HttpRequest(method=HttpMethod.GET, path=f"/projects/{ref}/database/schemas")
    return _handle_response(await ctx.dispatch(supabase_mgmt, req))


@tool(
    description="List installed database extensions",
    tags=["schema", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_extensions(ref: str) -> MgmtResult:
    ctx = get_context()
    req = HttpRequest(method=HttpMethod.GET, path=f"/projects/{ref}/database/extensions")
    return _handle_response(await ctx.dispatch(supabase_mgmt, req))


@tool(
    description="List database migrations",
    tags=["schema", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_migrations(ref: str) -> MgmtResult:
    ctx = get_context()
    req = HttpRequest(method=HttpMethod.GET, path=f"/projects/{ref}/database/migrations")
    return _handle_response(await ctx.dispatch(supabase_mgmt, req))


@tool(
    description="Apply a database migration (DDL)",
    tags=["schema", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def apply_migration(ref: str, name: str, sql: str) -> MgmtResult:
    ctx = get_context()
    req = HttpRequest(
        method=HttpMethod.POST,
        path=f"/projects/{ref}/database/migrations",
        body={"name": name, "sql": sql},
    )
    return _handle_response(await ctx.dispatch(supabase_mgmt, req))


@tool(
    description="Execute raw SQL against a project database with safety checks",
    tags=["sql", "write"],
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
async def execute_sql(ref: str, sql: str, *, continue_on_error: bool = False) -> MgmtResult:
    ctx = get_context()
    req = HttpRequest(
        method=HttpMethod.POST,
        path=f"/projects/{ref}/query",
        body={"query": sql, "continue_on_error": continue_on_error},
    )
    return _handle_response(await ctx.dispatch(supabase_mgmt, req))


@tool(
    description="List preview branches for a project",
    tags=["branches", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_branches(ref: str) -> MgmtResult:
    ctx = get_context()
    req = HttpRequest(method=HttpMethod.GET, path=f"/projects/{ref}/branches")
    return _handle_response(await ctx.dispatch(supabase_mgmt, req))


@tool(
    description="Create a preview branch for a project",
    tags=["branches", "write"],
    annotations=ToolAnnotations(readOnlyHint=False),
)
async def create_branch(ref: str, name: str, *, branch_from: str | None = None) -> MgmtResult:
    ctx = get_context()
    body: dict[str, Any] = {"name": name}
    if branch_from:
        body["branch_from"] = branch_from
    req = HttpRequest(method=HttpMethod.POST, path=f"/projects/{ref}/branches", body=body)
    return _handle_response(await ctx.dispatch(supabase_mgmt, req))


@tool(
    description="Get project logs (database, api, auth)",
    tags=["logs", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def get_logs(
    ref: str,
    log_type: str = "database",
    *,
    start_time: str | None = None,
    end_time: str | None = None,
) -> MgmtResult:
    ctx = get_context()
    path = f"/projects/{ref}/logs/{log_type}"
    query_params = []
    if start_time:
        query_params.append(f"start_time={start_time}")
    if end_time:
        query_params.append(f"end_time={end_time}")
    if query_params:
        path += "?" + "&".join(query_params)
    req = HttpRequest(method=HttpMethod.GET, path=path)
    return _handle_response(await ctx.dispatch(supabase_mgmt, req))


@tool(
    description="Get security and performance advisors for a project",
    tags=["advisors", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def get_advisors(ref: str, advisor_type: str = "security") -> MgmtResult:
    ctx = get_context()
    req = HttpRequest(method=HttpMethod.GET, path=f"/projects/{ref}/advisors/{advisor_type}")
    return _handle_response(await ctx.dispatch(supabase_mgmt, req))


@tool(
    description="Generate TypeScript types for a project database schema",
    tags=["codegen", "read"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def generate_typescript_types(ref: str, table_name: str | None = None) -> MgmtResult:
    ctx = get_context()
    path = f"/projects/{ref}/types/typescript"
    if table_name:
        path += f"?table={table_name}"
    req = HttpRequest(method=HttpMethod.GET, path=path)
    return _handle_response(await ctx.dispatch(supabase_mgmt, req))


mgmt_tools = [
    list_projects,
    get_project,
    list_organizations,
    list_tables,
    list_extensions,
    list_migrations,
    apply_migration,
    execute_sql,
    list_branches,
    create_branch,
    get_logs,
    get_advisors,
    generate_typescript_types,
]