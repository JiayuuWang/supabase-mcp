# Supabase MCP Server

A Supabase MCP server built with the [Dedalus MCP framework](https://dedaluslabs.ai). Provides secure access to Supabase databases via the PostgREST API and management APIs with credential encryption and JIT token exchange.

## Features

### Database Tools (PostgREST)

#### Read Operations

| Tool | Description |
|------|-------------|
| `db_select` | Select rows from a table with optional filters, ordering, and pagination |
| `db_get_by_id` | Get a single row by primary key |

#### Write Operations

| Tool | Description |
|------|-------------|
| `db_insert` | Insert one or more rows into a table |
| `db_update` | Update rows matching specified filters |
| `db_delete` | Delete rows matching specified filters |
| `db_upsert` | Insert or update rows on conflict |

#### RPC

| Tool | Description |
|------|-------------|
| `db_rpc` | Call a Supabase stored procedure/function |

### Management Tools (Management API)

#### Projects & Organizations

| Tool | Description |
|------|-------------|
| `list_projects` | List all Supabase projects |
| `get_project` | Get details of a specific project |
| `list_organizations` | List all organizations |

#### Schema & Migrations

| Tool | Description |
|------|-------------|
| `list_tables` | List database schemas |
| `list_extensions` | List installed database extensions |
| `list_migrations` | List database migrations |
| `apply_migration` | Apply a DDL migration |
| `execute_sql` | Execute raw SQL with safety checks |

#### Branches

| Tool | Description |
|------|-------------|
| `list_branches` | List preview branches |
| `create_branch` | Create a preview branch |

#### Logs & Advisors

| Tool | Description |
|------|-------------|
| `get_logs` | Get project logs (database, api, auth) |
| `get_advisors` | Get security and performance advisors |

#### Codegen

| Tool | Description |
|------|-------------|
| `generate_typescript_types` | Generate TypeScript types for database schema |

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Supabase project URL and API keys
- Dedalus API Key

## Setup

1. **Clone the repository**

```bash
git clone https://github.com/dedalus-labs/supabase-mcp.git
cd supabase-mcp
```

2. **Install dependencies**

```bash
uv sync
```

3. **Configure environment variables**

Create a `.env` file based on .env.example.

## Client Usage

```python
import asyncio
import os

from dotenv import load_dotenv
from dedalus_labs import AsyncDedalus, DedalusRunner
from dedalus_mcp.auth import Connection, SecretKeys, SecretValues

load_dotenv()

# Database connection (PostgREST)
supabase = Connection(
    name="supabase-mcp",
    secrets=SecretKeys(key="SUPABASE_SECRET_KEY"),
    base_url=f"{SUPABASE_URL}/rest/v1",
    auth_header_name="apikey",
    auth_header_format="{api_key}",
)

# Management API connection
supabase_mgmt = Connection(
    name="supabase-mcp-mgmt",
    secrets=SecretKeys(access_token="SUPABASE_ACCESS_TOKEN"),
    base_url="https://api.supabase.com/v1",
    auth_header_format="Bearer {api_key}",
)

# Bind credentials (encrypted client-side, decrypted at dispatch time)
db_secrets = SecretValues(supabase, key=os.getenv("SUPABASE_SECRET_KEY", ""))
mgmt_secrets = SecretValues(supabase_mgmt, access_token=os.getenv("SUPABASE_ACCESS_TOKEN", ""))

async def main():
    client = AsyncDedalus(
        api_key=os.getenv("DEDALUS_API_KEY"),
        base_url=os.getenv("DEDALUS_API_URL"),
        as_base_url=os.getenv("DEDALUS_AS_URL"),
    )
    runner = DedalusRunner(client)

    result = await runner.run(
        input="Select all rows from the users table, limit to 5.",
        model="anthropic/claude-sonnet-4-5",
        mcp_servers=["dedalus-labs/supabase-mcp"],
        credentials=[db_secrets, mgmt_secrets],
    )

    print(result.output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Security

DAuth ensures that your Supabase credentials are encrypted client-side and only decrypted inside a sealed execution boundary. Your server code, logs, and error traces never contain raw credentials.

## License

MIT License - see [LICENSE](LICENSE) for details.