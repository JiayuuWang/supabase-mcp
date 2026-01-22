# Supabase MCP Server

A Supabase MCP server built with the [Dedalus MCP framework](https://dedaluslabs.ai). Provides secure access to Supabase databases via the PostgREST API with credential encryption and JIT token exchange.

## Features

### Available Tools

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

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Supabase project URL and API key
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

SUPABASE_URL = os.getenv("SUPABASE_URL")

# Define the Supabase connection
supabase = Connection(
    name="supabase-mcp",
    secrets=SecretKeys(key="SUPABASE_SECRET_KEY"),
    base_url=f"{SUPABASE_URL}/rest/v1",
    auth_header_name="apikey",
    auth_header_format="{api_key}",
)

# Bind credentials (encrypted client-side, decrypted at dispatch time)
supabase_secrets = SecretValues(supabase, key=os.getenv("SUPABASE_SECRET_KEY", ""))

async def main():
    client = AsyncDedalus(
        api_key=os.getenv("DEDALUS_API_KEY"),
        base_url=os.getenv("DEDALUS_API_URL"),
        as_base_url=os.getenv("DEDALUS_AS_URL"),
    )
    runner = DedalusRunner(client)

    result = await runner.run(
        input="Select all rows from the users table, limit to 5.",
        model="openai/gpt-5",
        mcp_servers=["issac/supabase-mcp"],
        credentials=[supabase_secrets],
    )

    print(result.output)

if __name__ == "__main__":
    asyncio.run(main())
```

## License

MIT License - see [LICENSE](LICENSE) for details.
