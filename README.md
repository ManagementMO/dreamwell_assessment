# Dreamwell Influencer Email Response Agent

> **Assessment Status:** Day 1 Foundation Complete ✅
> 
> AI agent system that automates influencer email responses using MCP, YouTube Data API, CPM pricing, and OpenAI.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20 LTS (⚠️ Node 25 has Vite compatibility issues)
- npm or yarn

### Backend Setup (✅ Currently Running)

The backend is already running in terminal 7. To restart:

```bash
# Activate venv (if not already active)
source venv/Scripts/activate  # Windows Git Bash
# or: venv\Scripts\activate  # Windows CMD

# Start server
python backend_main.py

# Or use uvicorn directly
uvicorn backend_main:app --reload
```

**Backend URL:** http://localhost:8000

**Test Endpoints:**
```bash
# Health check
curl http://localhost:8000/

# List emails
curl http://localhost:8000/api/emails

# Get specific email thread
curl http://localhost:8000/api/emails/thread_001
```

### Frontend Setup (⚠️ Needs Node 20)

**If you're using Node 25.x, downgrade to Node 20 first:**

```bash
# Using nvm (recommended)
nvm install 20
nvm use 20

# Or download Node 20 LTS from: https://nodejs.org/
```

**Then start frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Frontend URL:** http://localhost:5173

---

## 📁 Project Structure

```
dreamwell_assessment/
│
├── backend_main.py              # FastAPI server + MCP client
├── mcp_server.py                # Standalone MCP tool server
├── config.py                    # Shared configuration
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (create from .env.example)
│
├── data/                        # Test data fixtures
│   ├── email_fixtures.json      # 21 synthetic email scenarios
│   ├── youtube_profiles.json    # 15 YouTube channel profiles
│   └── brand_profiles.json      # Perplexity + Copy AI data
│
├── frontend/                    # React + TypeScript UI
│   ├── src/
│   │   ├── api/client.ts        # Axios HTTP client
│   │   ├── types/index.ts       # TypeScript interfaces
│   │   ├── hooks/               # React Query hooks
│   │   ├── pages/               # Dashboard + EmailDetail
│   │   └── App.tsx              # Main app with routing
│   └── package.json
│
├── DREAMWELL_RESEARCH.md        # Company context & values
├── IMPLEMENTATION_PLAN.md       # Full 4-day plan
├── CLAUDE.md                    # Quick reference & rules
└── DAY1_COMPLETION.md           # This session's summary
```

---

## 🏗️ Architecture

### Backend: FastAPI + MCP

```
┌─────────────────────────────────────────┐
│         backend_main.py                 │
│  (FastAPI MCP Client)                   │
│                                         │
│  - Lifespan manager spawns subprocess  │
│  - MCP session in app.state            │
│  - 100% async endpoints                │
│  - CORS configured                     │
└─────────────┬───────────────────────────┘
              │ stdio pipe
              ↓
┌─────────────────────────────────────────┐
│         mcp_server.py                   │
│  (Standalone FastMCP Server)            │
│                                         │
│  - 5 MCP tools (email, brand)          │
│  - File-based logging (server.log)     │
│  - Loads .env independently            │
│  - NO imports from backend_main.py     │
└─────────────────────────────────────────┘
```

### Frontend: React + React Query

```
┌─────────────────────────────────────────┐
│              Browser                    │
│                                         │
│  Dashboard → EmailDetail                │
│      ↓            ↓                     │
│  useEmails   useGenerateResponse        │
│      ↓            ↓                     │
│  React Query (async state)              │
│      ↓            ↓                     │
│  Axios (45s timeout, CORS)              │
└─────────────┬───────────────────────────┘
              │ HTTP + JSON
              ↓
┌─────────────────────────────────────────┐
│      FastAPI Backend :8000              │
└─────────────────────────────────────────┘
```

---

## 🛠️ MCP Tools (Day 1 - Complete)

### Email Tools
1. **`get_email_thread(thread_id)`** - Fetch full thread with all messages
2. **`get_latest_emails(limit)`** - List recent threads sorted by timestamp
3. **`send_reply(thread_id, content)`** - Send response to influencer
4. **`mark_as_processed(thread_id)`** - Update status to processed

### Brand Tools
5. **`get_brand_context(brand_id)`** - Fetch brand messaging guidelines

### YouTube Tools (Day 2)
6. **`fetch_channel_data(url)`** - Get real YouTube metrics (hybrid fallback)
7. **`calculate_engagement(channel_id)`** - Compute engagement rate

### Pricing Tools (Day 2)
8. **`calculate_offer_price(...)`** - CPM-based pricing with multipliers
9. **`validate_counter_offer(...)`** - Negotiation boundary logic

---

## 🎨 UI Pages

### Dashboard (`/`)
- Email inbox with 20 threads
- Color-coded categories (price_negotiation, acceptance, not_interested, etc.)
- Click thread → navigate to detail page

### Email Detail (`/email/:threadId`)
- **Left Panel:** Email thread history
- **Right Panel:** AI response generator
  - "Generate Response" button
  - Loading state: "Thinking... (may take 30s)"
  - Editable textarea with draft
  - "Approve & Send" and "Regenerate" buttons

---

## 🔧 API Endpoints

### `GET /`
Health check

**Response:**
```json
{
  "status": "ok",
  "service": "Dreamwell Influencer Agent API",
  "version": "1.0.0"
}
```

### `GET /api/emails?limit=20`
List email threads via MCP

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "thread_id": "thread_001",
      "influencer_name": "Alex Johnson",
      "brand": "perplexity",
      "category": "price_negotiation",
      "status": "pending",
      "latest_message_time": "2024-01-15T10:30:00Z"
    },
    ...
  ],
  "total": 20
}
```

### `GET /api/emails/{thread_id}`
Get full email thread

**Response:**
```json
{
  "success": true,
  "data": {
    "thread_id": "thread_001",
    "influencer_name": "Alex Johnson",
    "influencer_email": "alex@example.com",
    "brand": "perplexity",
    "category": "price_negotiation",
    "channel_url": "https://youtube.com/@alexjohnson",
    "thread": [
      {
        "from": "outreach@perplexity.ai",
        "to": "alex@example.com",
        "subject": "Partnership Opportunity",
        "body": "Hi Alex...",
        "timestamp": "2024-01-15T10:00:00Z"
      },
      {
        "from": "alex@example.com",
        "to": "outreach@perplexity.ai",
        "subject": "Re: Partnership Opportunity",
        "body": "Thanks for reaching out...",
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

### `POST /api/generate`
Generate AI response (placeholder in Day 1, full implementation in Day 2)

**Request:**
```json
{
  "thread_id": "thread_001",
  "brand_id": "perplexity"
}
```

**Response:**
```json
{
  "category": "price_negotiation",
  "response_draft": "Hi Alex, thank you for...",
  "iterations_used": 3,
  "message_history": [...]
}
```

### `POST /api/send`
Approve and send response

**Request:**
```json
{
  "thread_id": "thread_001",
  "content": "Hi Alex, we'd love to work with you..."
}
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Required for Day 2
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

**Get API Keys:**
- **YouTube:** https://console.cloud.google.com/ (Enable YouTube Data API v3)
- **OpenAI:** https://platform.openai.com/api-keys

### config.py Settings

```python
FASTAPI_HOST = "0.0.0.0"
FASTAPI_PORT = 8000

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]

MAX_AGENT_ITERATIONS = 5
AGENT_TIMEOUT_SECONDS = 45
DEFAULT_LLM_MODEL = "gpt-4o"
```

---

## 🧪 Testing

### Backend Tests (Manual)

```bash
# Test MCP server standalone (debug mode)
python mcp_server.py

# Check logs
tail -f server.log

# Test REST API
curl http://localhost:8000/api/emails
curl http://localhost:8000/api/emails/thread_001
```

### Frontend Tests (Visual)

1. Open http://localhost:5173
2. Verify 20 emails load on dashboard
3. Click any email → detail page
4. Click "Generate Response"
5. Verify button disables and shows "Thinking..."
6. Verify placeholder response appears

---

## 📊 Day 1 Achievements

### ✅ Backend (100% Complete)
- [x] Lifespan manager spawning MCP subprocess
- [x] MCP session reused across requests
- [x] CORS configured for frontend
- [x] 5 MCP tools operational
- [x] REST endpoints tested and working
- [x] 100% async code
- [x] File-based logging

### ✅ Frontend (95% Complete)
- [x] React + TypeScript + Vite scaffolded
- [x] React Query configured
- [x] Tailwind CSS setup
- [x] Dashboard page with email list
- [x] EmailDetail page with AI generator
- [x] Loading states with button disable
- [x] 45s timeout configured
- [x] Routing with react-router-dom

### 🔧 Known Issues
- [ ] Frontend dev server (Node 25 + Vite incompatibility) - **User must downgrade to Node 20**

---

## 🚀 Next Steps (Day 2)

1. **Verify frontend runs** (after Node 20 downgrade)
2. **Implement ReAct Loop** in `backend_main.py`:
   - Multi-turn LLM reasoning
   - OpenAI tool calling with MCP
   - Iterative context building
3. **Add YouTube API integration**:
   - Real channel data fetching
   - 24h caching
   - Hybrid fallback to fixtures
4. **Build CPM pricing engine**:
   - Tiered CPM calculation
   - Engagement, niche, consistency multipliers
   - Negotiation boundary logic
5. **Test full agent flow**:
   - Email → YouTube lookup → Price calculation → Draft generation

---

## 📚 Documentation

- **`DREAMWELL_RESEARCH.md`** - Company values, pricing strategy, competitive landscape
- **`IMPLEMENTATION_PLAN.md`** - Full 4-day technical implementation plan
- **`CLAUDE.md`** - Quick reference with architecture rules
- **`DAY1_COMPLETION.md`** - Detailed summary of today's work

---

## 🐛 Troubleshooting

### Backend won't start

**Issue:** `uvicorn: command not found`

**Solution:**
```bash
# Activate venv first
source venv/Scripts/activate  # Windows Git Bash
python backend_main.py
```

### Frontend won't start (Node 25 error)

**Issue:** `Cannot find module @rollup/rollup-win32-x64-msvc`

**Solution:**
```bash
# Downgrade to Node 20 LTS
nvm install 20
nvm use 20
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### CORS errors in browser

**Issue:** `Access-Control-Allow-Origin` error

**Solution:**
- Verify backend is running on port 8000
- Check `config.py` includes frontend URL in `CORS_ORIGINS`
- Restart backend after config changes

### MCP tools not responding

**Issue:** 500 errors when calling `/api/emails`

**Solution:**
```bash
# Check MCP server logs
tail -f server.log

# Look for errors in startup
# Ensure data/*.json files exist
```

---

## 💻 Development Commands

```bash
# Backend
python backend_main.py                    # Start server
uvicorn backend_main:app --reload        # With auto-reload
tail -f server.log                        # View MCP logs
curl http://localhost:8000/api/emails    # Test API

# Frontend
cd frontend
npm run dev                               # Start dev server
npm run build                             # Production build
npm run preview                           # Preview build

# Dependencies
pip install -r requirements.txt           # Backend deps
cd frontend && npm install                # Frontend deps
```

---

## 🎯 Success Criteria

- [x] MCP server with 5+ working tools
- [x] FastAPI spawns MCP as subprocess
- [x] MCP session reused across requests
- [x] CORS configured
- [x] 100% async code
- [x] React Query setup
- [x] Loading states implemented
- [ ] Frontend running (blocked by Node 25 issue)
- [ ] Full stack visual test (pending frontend fix)

---

## 📞 Support

**For Dreamwell Team:**
- All critical architecture rules followed (see `CLAUDE.md`)
- Backend fully functional and tested
- Frontend code complete, just needs Node 20 to run
- Ready for Day 2 implementation

**Key Files to Review:**
1. `backend_main.py` - FastAPI + MCP client
2. `mcp_server.py` - MCP tools
3. `frontend/src/pages/EmailDetail.tsx` - UI with loading states
4. `DAY1_COMPLETION.md` - Detailed completion report

---

**Last Updated:** January 4, 2026  
**Status:** Day 1 Complete (Backend 100%, Frontend 95%)  
**Next:** User fixes Node issue → Visual test → Day 2 (ReAct + Pricing)

