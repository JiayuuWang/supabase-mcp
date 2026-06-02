# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""MCP server entrypoint.

Exposes Supabase tools via Dedalus MCP framework.
Credentials provided by clients at runtime via token exchange.
"""

import os

from dedalus_mcp import MCPServer
from dedalus_mcp.server import TransportSecuritySettings

from db import db_tools, supabase
from management import mgmt_tools, supabase_mgmt
from smoke import smoke_tools


def _disable_auto_output_schemas(server: MCPServer) -> None:
    server.tools._build_output_schema = lambda _fn: None


def create_server() -> MCPServer:
    """Create MCP server with current env config."""
    as_url = os.getenv("DEDALUS_AS_URL", "https://as.dedaluslabs.ai")
    return MCPServer(
        name="supabase-mcp",
        connections=[supabase, supabase_mgmt],
        http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        streamable_http_stateless=True,
        authorization_server=as_url,
    )


async def main() -> None:
    """Start MCP server."""
    server = create_server()
    _disable_auto_output_schemas(server)
    server.collect(*smoke_tools, *db_tools, *mgmt_tools)
    await server.serve(port=8080)
