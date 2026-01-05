# Dreamwell Influencer Email Response Agent - Implementation Plan

> **Context:** This is an internship assessment for Dreamwell AI, an influencer marketing automation platform focused on ROI-driven, transparent, automated campaign management.

---

## 🎯 Project Overview

Build an AI agent system that automates influencer email responses using:
- **MCP Server** for tool orchestration (standalone subprocess)
- **YouTube Data API v3** for real influencer data enrichment
- **CPM-based pricing engine** with transparent calculations
- **OpenAI/Claude LLM** for categorization and response generation
- **React UI** for testing and human approval workflow
- **Brand context** from Perplexity/Copy AI for personalized responses

**Tech Stack:** Python + FastAPI + React + MCP + OpenAI

---

## 🏗️ Critical Architecture Requirements

### ⚠️ MANDATORY - DO NOT DEVIATE

### 1. Strict File Separation

```
✅ CORRECT:
- mcp_server.py (standalone, uses FastMCP)
- backend_main.py (FastAPI, uses MCP Client)
- NO shared code except config.py

❌ WRONG:
- Importing tools from mcp_server.py into backend_main.py
- Shared utility functions between files
- Database models imported by both
```

### 2. MCP Server Lifecycle (Lifespan Manager Pattern)

```python
# backend_main.py - REQUIRED PATTERN

from fastapi import FastAPI
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: spawn mcp_server.py as subprocess
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            app.state.mcp_session = session  # CRITICAL: Store in app.state
            yield  # Server runs here
    # Shutdown automatic

app = FastAPI(lifespan=lifespan)
```

**Key Points:**
- MCP server spawned as subprocess on FastAPI startup
- Session stored in `app.state.mcp_session` for reuse
- Single session shared across all requests (NOT per-request)
- Cleanup automatic when FastAPI shuts down

### 3. 100% Async Pattern

```python
# ❌ WRONG - Blocking code
def get_emails():
    session = app.state.mcp_session
    result = session.call_tool("get_emails", {})  # BLOCKS
    return result

# ✅ CORRECT - Async all the way
async def get_emails():
    session = app.state.mcp_session
    result = await session.call_tool("get_emails", {})  # ASYNC
    return result

# All FastAPI endpoints MUST be async def
@app.get("/api/emails")
async def list_emails():  # async def required
    session = app.state.mcp_session
    emails = await session.call_tool("get_latest_emails", {"limit": 20})
    return emails

# OpenAI client MUST be async
from openai import AsyncOpenAI  # NOT OpenAI
client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
response = await client.chat.completions.create(...)  # await required
```

**Key Points:**
- ALL FastAPI endpoints: `async def`
- ALL MCP calls: `await session.call_tool()`
- ALL LLM calls: `await client.chat.completions.create()`
- NO blocking file I/O, network calls, or sleep()

### 4. OpenAI Tool Calling Integration

```python
# Step 1: Get MCP tools and convert to OpenAI schema
async def convert_mcp_tools_to_openai_schema(session: ClientSession) -> list:
    tools_list = await session.list_tools()

    openai_tools = []
    for tool in tools_list.tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema  # Already JSON Schema format
            }
        })
    return openai_tools

# Step 2: Call OpenAI with converted tools
openai_tools = await convert_mcp_tools_to_openai_schema(session)

response = await client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    tools=openai_tools,  # Pass MCP tools as OpenAI tools
    tool_choice="auto"
)

# Step 3: Execute tool calls via MCP
message = response.choices[0].message
if message.tool_calls:
    for tool_call in message.tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        # Execute via MCP (NOT directly!)
        result = await session.call_tool(tool_name, tool_args)
        # ... handle result ...
```

### 5. CORS Configuration (CRITICAL)

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan)

# ⚠️ MUST configure CORS IMMEDIATELY after app creation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6. React Loading States (CRITICAL)

```tsx
// useGenerateResponse.ts
export function useGenerateResponse() {
  return useMutation({
    mutationFn: async (request) => {
      const { data } = await api.post('/api/generate', request, {
        timeout: 45000  // 45 seconds timeout
      })
      return data
    }
  })
}

// EmailDetail.tsx
export function EmailDetail() {
  const { mutate, isPending, data, error } = useGenerateResponse()
  const [isButtonDisabled, setIsButtonDisabled] = useState(false)

  const handleGenerate = () => {
    setIsButtonDisabled(true)
    mutate(payload, {
      onSettled: () => {
        setIsButtonDisabled(false)  // Re-enable after success OR error
      }
    })
  }

  return (
    <button
      onClick={handleGenerate}
      disabled={isButtonDisabled || isPending}
    >
      {isPending ? (
        <>
          <Loader2 className="animate-spin mr-2" />
          Thinking... (may take 30s)
        </>
      ) : (
        'Generate Response'
      )}
    </button>
  )
}
```

### 7. React Query Configuration

```tsx
// main.tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,  // Don't refetch when user tabs back
      staleTime: 30000,  // Consider data fresh for 30s
    },
    mutations: {
      retry: 0,  // Don't retry failed generations
    }
  }
})
```

---

## 📁 Project Structure

```
dreamwell_assessment/
│
├── mcp_server.py                      # ⭐ STANDALONE MCP SERVER (FastMCP)
│                                      # - NO imports from backend_main.py
│                                      # - Contains ALL tool logic
│                                      # - Runs as subprocess via stdio
│
├── backend_main.py                    # ⭐ FASTAPI MCP CLIENT
│                                      # - Spawns mcp_server.py via stdio_client
│                                      # - Lifespan manager (startup/shutdown)
│                                      # - Agent orchestrator
│                                      # - REST API endpoints (all async)
│
├── config.py                          # Shared environment configuration
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
│
├── data/                              # Mock data (used by mcp_server.py)
│   ├── email_fixtures.json            # Synthetic test emails (20 scenarios)
│   ├── youtube_profiles.json          # Test YouTube channels (10 profiles)
│   └── brand_profiles.json            # Perplexity, Copy AI data
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── components/
│   │   │   ├── EmailThread/
│   │   │   ├── AgentStatus/
│   │   │   ├── ResponseEditor/
│   │   │   └── InfluencerCard/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   └── EmailDetail.tsx
│   │   ├── hooks/
│   │   │   ├── useEmails.ts           # react-query hook
│   │   │   └── useGenerateResponse.ts # react-query hook
│   │   ├── api/
│   │   │   └── client.ts              # Axios with CORS handling
│   │   └── types/
│   │       └── index.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── tests/
│   ├── test_mcp_tools.py
│   ├── test_agent.py
│   └── test_integration.py
│
├── docs/
│   ├── PRICING_STRATEGY.md
│   └── API.md
│
├── DREAMWELL_RESEARCH.md              # Company research & context
└── IMPLEMENTATION_PLAN.md             # This file
```

---

## 📋 Implementation Phases

### Phase 0: Foundation (Day 1)

**Goal:** Project setup and configuration (NO DATABASE - using JSON fixtures)

**Tasks:**
- [ ] Initialize Python venv (Python 3.11+)
- [ ] Create `requirements.txt`:
  ```
  fastapi[all]
  mcp
  openai
  google-api-python-client
  uvicorn
  pydantic
  python-dotenv
  ```
- [ ] Create `config.py`:
  ```python
  import os
  from dotenv import load_dotenv

  load_dotenv()

  # API Keys
  YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
  OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

  # Paths
  DATA_DIR = "data"
  EMAIL_FIXTURES_PATH = f"{DATA_DIR}/email_fixtures.json"
  YOUTUBE_PROFILES_PATH = f"{DATA_DIR}/youtube_profiles.json"
  BRAND_PROFILES_PATH = f"{DATA_DIR}/brand_profiles.json"

  # Server Config
  FASTAPI_PORT = 8000
  CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]
  ```
- [ ] Create `.env.example`
- [ ] Create `data/` directory with placeholder JSON files
- [ ] Initialize frontend:
  ```bash
  npm create vite@latest frontend -- --template react-ts
  cd frontend
  npm install @tanstack/react-query axios lucide-react
  npm install -D tailwindcss postcss autoprefixer
  npx tailwindcss init -p
  ```

**Deliverables:**
- Working Python environment
- Config system ready
- Frontend scaffolded

---

### Phase 1: Standalone MCP Server (Days 2-3)

**Goal:** Build self-contained MCP tool server using FastMCP

**⚠️ CRITICAL: Single file, no imports from FastAPI**
**⚠️ CRITICAL: Configure logging to file, NOT stdout/stderr (breaks stdio pipe)**

**Day 2 - MCP Server Setup + Email/Brand Tools:**

Create `mcp_server.py`:

```python
from mcp.server.fastmcp import FastMCP
import json
import logging
import config

# ⚠️ CRITICAL: Configure logging to write to file, NOT stdout/stderr
# Writing to stdout/stderr will break the MCP stdio pipe!
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='server.log',  # Write to file only
    filemode='a'
)
logger = logging.getLogger(__name__)

# DO NOT use print() or logging to console - it breaks stdio!
logger.info("MCP server starting...")

# Initialize FastMCP server
mcp = FastMCP("Dreamwell Influencer Agent")

# Load data from JSON
emails = json.load(open(config.EMAIL_FIXTURES_PATH))
youtube_profiles = json.load(open(config.YOUTUBE_PROFILES_PATH))
brands = json.load(open(config.BRAND_PROFILES_PATH))

logger.info("Data loaded successfully")

@mcp.tool()
def get_email_thread(thread_id: str) -> dict:
    """Get full email thread history"""
    logger.info(f"Fetching email thread: {thread_id}")
    # Implementation...
    pass

@mcp.tool()
def get_latest_emails(limit: int = 10) -> list:
    """List recent email threads"""
    logger.info(f"Fetching {limit} latest emails")
    # Implementation...
    pass

# ... more tools ...
```

**Implement:**
- [ ] **CRITICAL:** Configure Python logging module to write to `server.log` file
- [ ] **CRITICAL:** DO NOT write debug logs to stdout/stderr - this breaks the MCP stdio pipe
- [ ] Use `logger.info()`, `logger.debug()`, etc. for debugging (writes to file)
- [ ] Email tools (4): get_email_thread, get_latest_emails, send_reply, mark_as_processed
- [ ] Brand tools (1): get_brand_context
- [ ] Test standalone: `python mcp_server.py` (check server.log for output)

**Day 3 - YouTube & Pricing Tools:**

**Implement:**
- [ ] YouTube API client with 24h caching
- [ ] YouTube tools (2): fetch_channel_data, calculate_engagement

  **Hybrid Fallback Strategy:**
  The `fetch_channel_data` tool must implement this logic:
  1. Check if `YOUTUBE_API_KEY` exists.
  2. If yes, try to fetch from real API.
  3. If API fails (quota/error) OR key is missing, **fallback silently** to `data/youtube_profiles.json`.
  4. **Never crash** if the API is down.

- [ ] CPM pricing logic (4 functions):
  - `calculate_base_cpm(subscribers)`
  - `calculate_engagement_multiplier(engagement_rate)`
  - `calculate_niche_multiplier(category, brand_vertical)`
  - `calculate_consistency_multiplier(video_history)`
- [ ] Pricing tools (2): calculate_offer_price, validate_counter_offer

**Deliverables:**
- Single `mcp_server.py` file (~500-800 lines)
- 10+ MCP tools fully functional
- Runs independently as subprocess

---

### Phase 2: Pricing Strategy (Day 4)

**Goal:** Production-ready CPM pricing engine

**CPM Tiers:**
- Micro (1K-10K): $10-15 CPM
- Mid (10K-100K): $15-25 CPM
- Macro (100K-1M): $25-40 CPM
- Mega (1M+): $40-100 CPM

**Multipliers:**
- Engagement (<5%: 0.7x, 5-15%: 1.0x, 15-30%: 1.3x, >30%: 1.5x)
- Niche (Tech/AI: 1.2x, Finance: 1.4x, Lifestyle: 1.0x, Gaming: 0.9x)
- Consistency (High: 1.1x, Medium: 1.0x, Low: 0.9x)

**Negotiation:**
- ±10%: Auto-accept
- ±20%: Accept with explanation
- 20-40%: Counter-offer
- >40%: Polite decline

**Tasks:**
- [ ] Implement tiered CPM calculation
- [ ] Implement all multipliers
- [ ] Define negotiation boundaries
- [ ] Create `docs/PRICING_STRATEGY.md`

---

### Phase 3: FastAPI Backend + Lifespan Manager (Days 5-6)

**Goal:** Build MCP client with async agent orchestration

**Day 5 - Lifespan Manager + MCP Client:**

Create `backend_main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            app.state.mcp_session = session
            print("✅ MCP server started")
            yield
            print("🛑 MCP server shutting down")

app = FastAPI(lifespan=lifespan)

# CRITICAL: Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Day 6 - Agent Orchestrator + OpenAI (ReAct Loop Pattern):**

```python
from openai import AsyncOpenAI
import json

client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

def mcp_tool_to_openai_schema(mcp_tool) -> dict:
    """
    Robust utility to convert MCP tool schema to OpenAI function schema.
    Handles type mapping differences between MCP JSON Schema and OpenAI format.
    """
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description,
            "parameters": mcp_tool.inputSchema  # MCP uses JSON Schema (compatible)
        }
    }

async def convert_mcp_tools_to_openai_schema(session):
    """Get all MCP tools and convert to OpenAI format"""
    tools_list = await session.list_tools()
    return [mcp_tool_to_openai_schema(tool) for tool in tools_list.tools]

async def agent_orchestrator(email_context, brand_id):
    """
    ReAct Loop Pattern: Reasoning and Acting in multi-turn conversation.

    The agent iteratively:
    1. Reasons about what to do next (LLM call)
    2. Acts by calling tools (MCP session)
    3. Observes results and adds to context
    4. Repeats until task is complete or max iterations reached
    """
    session = app.state.mcp_session
    openai_tools = await convert_mcp_tools_to_openai_schema(session)

    # Initialize message history
    messages = [
        {
            "role": "system",
            "content": f"""You are an influencer outreach assistant for {brand_id}.
            Analyze the email and use available tools to:
            1. Get the email thread context
            2. Fetch YouTube channel data for the influencer
            3. Calculate fair CPM-based pricing
            4. Validate any counter-offers if present
            5. Generate an appropriate response

            Work step-by-step using the available tools."""
        },
        {
            "role": "user",
            "content": json.dumps(email_context)
        }
    ]

    # ReAct Loop: Max 5 iterations to prevent infinite loops
    MAX_ITERATIONS = 5
    for iteration in range(MAX_ITERATIONS):
        # Step 1: Call LLM with current context
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=openai_tools,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        # Step 2: Check if LLM wants to call tools
        if not assistant_message.tool_calls:
            # No more tool calls - agent is done reasoning
            break

        # Step 3: Execute each tool call via MCP
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            # Step 4: Call MCP tool (async!)
            result = await session.call_tool(tool_name, tool_args)

            # Step 5: Append tool result to message history
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(result)
            })

        # Loop continues - LLM will see tool results and decide next action

    # Extract final response from last assistant message
    final_response = messages[-1].content if messages[-1].role == "assistant" else None

    return {
        "category": "price_negotiation",  # Extract from LLM response
        "response_draft": final_response,
        "iterations_used": iteration + 1,
        "message_history": messages  # For debugging
    }

@app.post("/api/generate")
async def generate_response(request: dict):
    """Main agent endpoint - uses ReAct loop for multi-turn reasoning"""
    result = await agent_orchestrator(
        email_context=request["email"],
        brand_id=request.get("brand_id", "perplexity")
    )
    return result

@app.get("/api/emails")
async def list_emails():
    """List all emails via MCP tool"""
    session = app.state.mcp_session
    emails = await session.call_tool("get_latest_emails", {"limit": 20})
    return emails
```

**Tasks:**
- [ ] Implement lifespan manager
- [ ] Configure CORS
- [ ] **Create robust `mcp_tool_to_openai_schema()` utility** to handle type mapping
- [ ] **Implement ReAct Loop Pattern** with while loop (max 5 iterations):
  - [ ] Call LLM with current message history
  - [ ] Check for `tool_calls` in response
  - [ ] Execute tools via `await session.call_tool()`
  - [ ] Append tool results to message history
  - [ ] Loop back to LLM with updated context
  - [ ] Break when no more tool calls (agent is done)
- [ ] Implement REST endpoints (all async def)
- [ ] Test: `uvicorn backend_main:app --reload`

**Deliverables:**
- `backend_main.py` with lifespan manager
- MCP session reused across requests
- 100% async
- OpenAI tool calling integrated
- CORS configured

---

### Phase 4: Pricing Strategy Documentation (Day 7)

**Tasks:**
- [ ] Create comprehensive `docs/PRICING_STRATEGY.md`
- [ ] Validate pricing logic matches documentation
- [ ] Create test cases for edge cases

---

### Phase 5: React Frontend with Loading States (Days 8-9)

**Goal:** Build robust UI with react-query and timeout handling

**Day 8 - Setup + React Query:**

**Configure React Query:**
```tsx
// main.tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30000,
    },
    mutations: { retry: 0 }
  }
})
```

**Create API Client:**
```tsx
// api/client.ts
export const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 45000,
})
```

**Create Hooks:**
```tsx
// hooks/useEmails.ts
export function useEmails() {
  return useQuery({
    queryKey: ['emails'],
    queryFn: async () => {
      const { data } = await api.get('/api/emails')
      return data
    },
    staleTime: 60000,
  })
}

// hooks/useGenerateResponse.ts
export function useGenerateResponse() {
  return useMutation({
    mutationFn: async (request) => {
      const { data } = await api.post('/api/generate', request)
      return data
    }
  })
}
```

**Day 9 - Components:**

**Tasks:**
- [ ] Create EmailThread component
- [ ] Create InfluencerCard component
- [ ] Create PricingBreakdown component
- [ ] Create ResponseEditor component:
  - Must be a `<textarea>` or Rich Text Editor (not read-only)
  - Pre-filled with the Agent's draft
  - User must be able to **edit** the draft manually
  - Add a "Send / Approve" button (calls `mark_as_processed` tool)
- [ ] Create Dashboard page with useEmails
- [ ] Create EmailDetail page with:
  - Button disable when isPending
  - "Thinking... (may take 30s)" indicator
  - 45s timeout handling
  - onSettled to re-enable button

**Deliverables:**
- React app with react-query
- Robust loading states
- Timeout handling (45s)
- Button disabled during processing

---

### Phase 6: Testing & Data (Day 10)

**Tasks:**
- [ ] Create 20+ synthetic email scenarios:
  - 5 not_interested
  - 6 price_negotiation (±10%, ±25%, ±50%)
  - 3 acceptance
  - 4 bulk_deal
  - 2 clarification
- [ ] Create 10 YouTube channel profiles
- [ ] Run integration tests
- [ ] Validate >90% categorization accuracy
- [ ] Test edge cases
- [ ] Write comprehensive README

---

### Phase 7: Polish & Demo (Day 11)

**Tasks:**
- [ ] Add loading states, error messages
- [ ] Optimize performance
- [ ] Create demo script
- [ ] Prepare talking points
- [ ] Final testing pass

---

## 💡 CPM Pricing Formula

```python
final_cpm = base_cpm × engagement_multiplier × niche_multiplier × consistency_multiplier

total_price = (expected_views / 1000) × final_cpm

negotiation_range = total_price ± 20%
```

**Base CPM by Tier:**
- Micro (1K-10K): $10-15
- Small (10K-50K): $15-20
- Mid (50K-100K): $20-25
- Macro (100K-500K): $25-40
- Large (500K-1M): $40-60
- Mega (1M+): $60-100

**Engagement Multiplier:**
- <5%: 0.7x (red flag)
- 5-15%: 1.0x
- 15-30%: 1.3x
- >30%: 1.5x

**Niche Multiplier:**
- Tech/AI: 1.2x (Perplexity/Copy AI target)
- Finance: 1.4x
- B2B/Productivity: 1.2x
- Lifestyle: 1.0x
- Gaming: 0.9x

**Consistency Multiplier:**
- High: 1.1x
- Medium: 1.0x
- Low: 0.9x

---

## 🎯 Success Criteria

### Must-Have
- [ ] MCP server with 10+ working tools
- [ ] Agent categorizes 18/20 test emails correctly (90%)
- [ ] Agent successfully handles multi-turn reasoning (e.g., Get Email → Get Stats → Calculate Price → Draft Response)
- [ ] Pricing engine produces consistent CPMs
- [ ] YouTube API fetches real data
- [ ] React UI shows full flow
- [ ] All responses include pricing breakdown
- [ ] Negotiation follows defined boundaries
- [ ] Handles edge cases gracefully

### Performance Targets
- **Categorization Accuracy:** >90%
- **Response Quality:** >85% approval
- **Pricing Accuracy:** ±5% of manual calculation
- **Processing Speed:** <10 seconds per email
- **Tool Call Success:** >95%

---

## 📝 Critical Implementation Files

### Backend (2 files only)

1. **`mcp_server.py`** (~500-800 lines) ⭐ MOST CRITICAL
   - Standalone FastMCP server
   - Contains ALL tool logic
   - NO imports from backend_main.py
   - Runs as independent subprocess

2. **`backend_main.py`** (~300-400 lines)
   - FastAPI with lifespan manager
   - MCP Client (stdio_client)
   - Agent orchestrator
   - REST API endpoints (all async)
   - CORS configuration

### Frontend (3 critical files)

3. **`frontend/src/hooks/useGenerateResponse.ts`**
   - React Query mutation hook
   - 45s timeout
   - Error handling

4. **`frontend/src/pages/EmailDetail.tsx`**
   - Loading state implementation
   - Button disable + spinner

5. **`frontend/src/components/ResponseEditor/ResponseEditor.tsx`**
   - Pricing breakdown display
   - Approval workflow

---

## 🚨 Architecture Validation Checklist

Before implementation:

- [ ] mcp_server.py is completely standalone (no FastAPI imports)
- [ ] backend_main.py spawns mcp_server.py as subprocess via stdio
- [ ] MCP session initialized once at startup (lifespan manager)
- [ ] Session stored in app.state, reused across requests
- [ ] ALL Python code is async (no blocking operations)
- [ ] MCP tools converted to OpenAI schemas dynamically
- [ ] LLM calls MCP tools via session.call_tool()
- [ ] CORS configured immediately after FastAPI app creation
- [ ] React uses react-query for all server state
- [ ] Loading states with button disable + spinner
- [ ] Timeout handling for 30+ second processing
- [ ] useEmails doesn't refetch unnecessarily

---

## 🎬 Demo Strategy

**Opening (30s):**
"AI agent system for Dreamwell that automates influencer email responses using MCP, real YouTube data, and transparent CPM pricing."

**Flow (3-4 min):**
1. Dashboard → select price negotiation email
2. Watch agent process in real-time
3. Show YouTube metrics fetched
4. Display CPM calculation breakdown
5. Review generated response
6. Approve and explain pricing transparency
7. Quick demo of acceptance flow

**Closing (30s):**
"Embodies Dreamwell values: automation (90% workflow), transparency (clear pricing), ROI-focus (data-driven). Scales from 5 to 200+ influencers."

---

## 📚 Additional Resources

- **DREAMWELL_RESEARCH.md** - Company context, values, competitive landscape
- **docs/PRICING_STRATEGY.md** - Detailed pricing formulas and examples (to be created)
- **docs/API.md** - REST API documentation (to be created)

---

## ⏱️ Timeline - 4-Day Vertical Slice Sprint

**Total:** 4 days (compressed from 11-day plan for rapid execution)

### Day 1: The Skeleton (Get the Pipes Working)
- Mock data fixtures (emails, YouTube profiles, brands)
- Standalone MCP server with basic tools
- FastAPI with lifespan manager + MCP connection
- Basic React UI shell
- **Goal:** End-to-end "hello world" - button click → MCP tool call → response

### Day 2: The Brains (Intelligence Layer)
- ReAct Loop implementation (multi-turn reasoning)
- Real YouTube Data API v3 integration
- CPM pricing math with all multipliers
- Negotiation logic
- **Goal:** Agent can think step-by-step and make pricing decisions

### Day 3: The Polish (User Experience)
- React loading states (button disable, spinner, timeout)
- UI styling with Tailwind
- Pricing breakdown component
- Edge case handling (deleted channels, API errors, timeouts)
- **Goal:** Production-quality UX

### Day 4: Testing & Demo (Validation)
- Final integration tests
- Synthetic email scenarios (20+)
- >90% categorization accuracy validation
- Demo recording
- **Goal:** Deliverable ready for submission

---

## 🔄 Version History

- **v1.0** - Initial implementation plan created (Jan 4, 2026)
- Based on Dreamwell assessment requirements
- Incorporates critical architectural constraints
- Ready for execution

---

**Last Updated:** January 4, 2026
**Status:** Ready for implementation
**Next Action:** Begin Phase 0 - Foundation
