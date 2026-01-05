# Claude Code Session Memory - Dreamwell Assessment

> **Quick Reference:** Essential information for any coding agent working on this project

---

## 🎯 What We're Building

An **AI agent system** that automates influencer email responses for Dreamwell AI's internship assessment.

**Core Function:** Process influencer emails → Fetch YouTube data → Calculate CPM pricing → Generate contextual responses → Present for human approval

---

## 🏗️ Architecture - THE RULES

### ⚠️ CRITICAL: Do NOT break these rules

1. **TWO Python files ONLY:**
   - `mcp_server.py` - Standalone FastMCP server (NO imports from FastAPI)
   - `backend_main.py` - FastAPI app that spawns mcp_server.py as subprocess

2. **Process Communication:**
   - FastAPI spawns MCP server via `stdio_client` on startup
   - Uses lifespan manager
   - Session stored in `app.state.mcp_session`
   - ONE session shared across ALL requests

3. **Logging in MCP Server:**
   - ⚠️ CRITICAL: Use file-based logging ONLY (server.log)
   - DO NOT write to stdout/stderr (breaks stdio pipe!)
   - Configure: `logging.basicConfig(filename='server.log', ...)`

4. **100% Async:**
   - ALL endpoints: `async def`
   - ALL MCP calls: `await session.call_tool()`
   - ALL LLM calls: `await client.chat.completions.create()`

5. **CORS is MANDATORY:**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000", "http://localhost:5173"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

6. **React Loading States:**
   - Button MUST disable on click
   - Show "Thinking... (may take 30s)" indicator
   - 45s timeout on axios
   - Use react-query's `isPending`
   - Use `onSettled` (not `onSuccess`)

7. **Env Vars in Subprocess:**
   - `mcp_server.py` MUST call `load_dotenv()` immediately at the top of the file
   - Do not rely on the parent process to pass environment variables

---

## 📁 File Structure

```
dreamwell_assessment/
├── mcp_server.py           # ⭐ Standalone MCP server (FastMCP)
├── backend_main.py         # ⭐ FastAPI client (spawns MCP server)
├── config.py               # Shared env config
├── requirements.txt        # Python deps
├── .env.example
├── data/
│   ├── email_fixtures.json
│   ├── youtube_profiles.json
│   └── brand_profiles.json
├── frontend/               # React + TypeScript + Vite
│   ├── src/
│   │   ├── hooks/
│   │   │   ├── useEmails.ts
│   │   │   └── useGenerateResponse.ts
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   └── EmailDetail.tsx
│   │   ├── components/
│   │   │   ├── ResponseEditor/
│   │   │   ├── EmailThread/
│   │   │   └── PricingBreakdown/
│   │   └── api/client.ts
├── DREAMWELL_RESEARCH.md   # Company context
├── IMPLEMENTATION_PLAN.md  # Detailed plan
└── CLAUDE.md              # This file
```

---

## 🔧 Tech Stack

**Backend:**
- FastAPI (async)
- MCP (Model Context Protocol)
- OpenAI API (gpt-4o)
- Google YouTube Data API v3
- Python 3.11+

**Frontend:**
- React 18 + TypeScript
- Vite
- React Query (@tanstack/react-query)
- Axios
- Tailwind CSS

---

## 🎨 Data Flow

```
1. User clicks "Generate Response" in React
   ↓
2. Button disabled + "Thinking..." shown
   ↓
3. POST /api/generate → FastAPI backend
   ↓
4. Agent orchestrator (ReAct Loop - max 5 iterations):
   - await session.list_tools() → Get MCP tools
   - Convert to OpenAI tool schemas
   - LOOP START:
     • await openai.chat.completions.create(tools=...)
     • LLM reasons about what to do next
     • If tool_calls exist:
       - await session.call_tool() for each (YouTube, pricing, etc.)
       - Append tool results to message history
       - LOOP BACK (until done or max iterations)
     • Else: Generate final response
   ↓
5. Return JSON to React
   ↓
6. Display response + pricing breakdown
   ↓
7. Re-enable button
```

---

## 💰 CPM Pricing (Core Differentiator)

```python
final_cpm = base_cpm × engagement_multiplier × niche_multiplier × consistency_multiplier
total_price = (expected_views / 1000) × final_cpm
```

**Base CPM Tiers:**
- Micro (1K-10K): $10-15
- Mid (10K-100K): $15-25
- Macro (100K-1M): $25-40
- Mega (1M+): $40-100

**Multipliers:**
- Engagement: <5%=0.7x, 5-15%=1.0x, 15-30%=1.3x, >30%=1.5x
- Niche: Tech/AI=1.2x, Finance=1.4x, Lifestyle=1.0x, Gaming=0.9x
- Consistency: High=1.1x, Medium=1.0x, Low=0.9x

**Negotiation:**
- ±10%: Auto-accept
- ±20%: Accept with explanation
- 20-40%: Counter-offer
- >40%: Decline

---

## 🛠️ MCP Tools (10+ required)

### Email Tools (4)
1. `get_email_thread(thread_id)` → full thread
2. `get_latest_emails(limit)` → list emails
3. `send_reply(thread_id, content)` → send
4. `mark_as_processed(thread_id)` → update status

### YouTube Tools (2)
5. `fetch_channel_data(url)` → subs, views, videos
6. `calculate_engagement(channel_id)` → metrics

### Pricing Tools (2)
7. `calculate_offer_price(channel_url, campaign_type, brand_id)` → price breakdown
8. `validate_counter_offer(channel_url, original, counter)` → accept/reject/counter

### Brand Tools (1)
9. `get_brand_context(brand_id)` → Perplexity or Copy AI data

---

## 📦 Dependencies

**Python (`requirements.txt`):**
```
fastapi[all]
mcp
openai
google-api-python-client
uvicorn
pydantic
python-dotenv
```

**Frontend (`package.json`):**
```
@tanstack/react-query
axios
lucide-react
tailwindcss
```

---

## 🔑 Environment Variables

**.env.example:**
```
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

---

## 🧪 Test Data Requirements

**Email Scenarios (20 total):**
- 5 not_interested (polite decline, busy, mismatch, competitor, hostile)
- 6 price_negotiation (+8%, +18%, +35%, +60%, -10%, vague)
- 3 acceptance (enthusiastic, conditional, quick yes)
- 4 bulk_deal (3-video, monthly, combo, unreasonable)
- 2 clarification (product questions, creative freedom)

**YouTube Profiles (10 total):**
- Micro high engagement: 8K subs, 75% engagement
- Mid-tier tech: 75K subs, 20% engagement
- Macro: 150K subs, 20% engagement
- Mega low engagement: 1.5M subs, 3.3% (red flag)
- Declining: 200K subs, views dropped 80%
- Rising star: 2K subs, 75% engagement
- Finance niche: 300K subs (1.4x multiplier)
- Gaming: 500K subs (0.9x multiplier)
- Inconsistent: 50K subs, erratic views
- Perfect: 100K subs, 25% engagement, AI niche

**Brand Profiles (2):**
- Perplexity: AI search, $50K budget, tech audience
- Copy AI: AI writing, $75K budget, marketer audience

---

## ✅ Success Criteria

- [ ] MCP server with 10+ tools
- [ ] >90% email categorization accuracy (18/20)
- [ ] Multi-turn reasoning (Get Email → Get Stats → Calculate Price → Draft Response)
- [ ] Consistent CPM calculations
- [ ] Real YouTube API integration
- [ ] Full React UI flow
- [ ] Pricing breakdown in all responses
- [ ] Proper negotiation boundaries
- [ ] Edge case handling

---

## 🚀 Quick Start Commands

**Backend:**
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn backend_main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Test MCP Server Standalone:**
```bash
python mcp_server.py
```

---

## 🎯 Dreamwell Alignment

**Values to Demonstrate:**
- ✅ **Automation:** 90% of workflow automated
- ✅ **Transparency:** Clear CPM breakdowns
- ✅ **Data-Driven:** YouTube metrics over vanity
- ✅ **ROI-Focus:** Negotiation boundaries protect budget
- ✅ **Practical:** Working system, not just theory

**Tech Alignment:**
- ✅ React frontend (their stack)
- ✅ AI-first approach (fits their clients)
- ✅ Scalable architecture (MCP enables growth)

---

## 🐛 Common Pitfalls to Avoid

1. **Importing MCP tools into FastAPI** ❌
   - Keep mcp_server.py standalone
   - Communicate via stdio only

2. **Blocking code** ❌
   - Use `async def` everywhere
   - Use `await` for all I/O

3. **Forgetting CORS** ❌
   - Frontend will fail silently
   - Configure immediately after app creation

4. **No loading states** ❌
   - Agent takes 30+ seconds
   - Must disable button + show indicator

5. **React Query refetching** ❌
   - Set `refetchOnWindowFocus: false`
   - Set appropriate `staleTime`

6. **Per-request MCP sessions** ❌
   - ONE session for entire app lifetime
   - Stored in `app.state.mcp_session`

---

## 📞 Where to Get Help

- **DREAMWELL_RESEARCH.md** - Company context and values
- **IMPLEMENTATION_PLAN.md** - Detailed 4-day vertical slice sprint
- **docs/PRICING_STRATEGY.md** - CPM formula details (to be created)
- **docs/API.md** - REST API docs (to be created)

---

## 📈 Current Status

**Sprint:** Ready to begin Day 1 (The Skeleton)

**Next Steps:**
1. Initialize Python environment
2. Create config.py and requirements.txt
3. Create mock data (email_fixtures.json, youtube_profiles.json, brand_profiles.json)
4. Build standalone mcp_server.py with FastMCP
5. Build backend_main.py with lifespan manager
6. Initialize React frontend with basic UI

---

## 💡 Quick Tips

- **Testing MCP tools:** Use MCP Inspector
- **Testing agent:** Use curl or Postman on /api/generate
- **Debugging async:** Use `asyncio.create_task()` for background tasks
- **YouTube API quota:** 10,000 units/day, cache aggressively (24h)
- **LLM costs:** gpt-4o is expensive, consider caching tool results

---

**Version:** 1.0
**Last Updated:** January 4, 2026
**Status:** Ready for implementation
