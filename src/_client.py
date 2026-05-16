# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Test client for Supabase MCP server.

Exercises all tools: db_*, mgmt_*, smoke_tools.
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

DEDALUS_API_KEY = os.getenv("DEDALUS_API_KEY", "")
DEDALUS_API_URL = os.getenv("DEDALUS_API_URL", "https://api.dedaluslabs.ai")
DEDALUS_AS_URL = os.getenv("DEDALUS_AS_URL", "https://as.dedaluslabs.ai")


async def main() -> None:
    from dedalus_labs import AsyncDedalus, DedalusRunner
    from dedalus_mcp.auth import Connection, SecretKeys, SecretValues

    from db import supabase
    from management import supabase_mgmt

    if not DEDALUS_API_KEY:
        print("Error: DEDALUS_API_KEY not set")
        return

    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")
    SUPABASE_ACCESS_TOKEN = os.getenv("SUPABASE_ACCESS_TOKEN", "")

    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        print("Error: SUPABASE_URL and SUPABASE_SECRET_KEY must be set")
        return

    db_secrets = SecretValues(supabase, key=SUPABASE_SECRET_KEY)
    mgmt_secrets = SecretValues(supabase_mgmt, access_token=SUPABASE_ACCESS_TOKEN)

    client = AsyncDedalus(
        api_key=DEDALUS_API_KEY,
        base_url=DEDALUS_API_URL,
        as_base_url=DEDALUS_AS_URL,
    )
    runner = DedalusRunner(client)

    print("Testing Supabase MCP server...")
    print(f"  Project URL: {SUPABASE_URL}")

    result = await runner.run(
        input="List all tables in the public schema, limit to 5.",
        model="anthropic/claude-sonnet-4-5",
        mcp_servers=["dedalus-labs/supabase-mcp"],
        credentials=[db_secrets, mgmt_secrets],
    )

    print(f"\nResult:\n{result.output}")


if __name__ == "__main__":
    asyncio.run(main())