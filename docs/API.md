# Dreamwell Agent - API Documentation

> **Base URL:** `http://localhost:8000/api`

---

## Overview

The Dreamwell backend exposes a REST API for the React frontend, powered by FastAPI with an MCP (Model Context Protocol) server handling tool execution.

---

## Authentication

Currently running in development mode without authentication. Production would use JWT tokens.

---

## Endpoints

### 1. List Emails

```http
GET /emails?limit={limit}
```

**Description:** Returns a list of email threads from the inbox.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `limit` | int | 20 | Maximum threads to return |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "thread_id": "thread_001",
      "influencer_name": "Alex Chen",
      "brand": "perplexity",
      "category": "price_negotiation",
      "status": "pending",
      "latest_message_time": "2024-01-15T14:20:00Z"
    }
  ],
  "total": 21
}
```

---

### 2. Get Email Thread

```http
GET /emails/{thread_id}
```

**Description:** Returns the full email thread with all messages.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `thread_id` | string | Thread identifier |

**Response:**
```json
{
  "success": true,
  "data": {
    "thread_id": "thread_001",
    "category": "price_negotiation",
    "influencer_name": "Alex Chen",
    "influencer_email": "alex@techreview.com",
    "youtube_channel_url": "https://www.youtube.com/@TechReviewAlex",
    "brand": "perplexity",
    "status": "pending",
    "thread": [
      {
        "from": "outreach@perplexity.ai",
        "to": "alex@techreview.com",
        "subject": "Partnership Opportunity",
        "body": "...",
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

---

### 3. Generate AI Response

```http
POST /generate
```

**Description:** Triggers the AI agent to analyze the email and generate a response using the ReAct loop pattern.

**Request Body:**
```json
{
  "thread_id": "thread_001",
  "brand_id": "perplexity"
}
```

**Response:**
```json
{
  "category": "negotiation",
  "response_draft": "Hi Alex,\n\nThank you for your interest...",
  "pricing_breakdown": {
    "metrics": {
      "subscribers": 100000,
      "avg_views": 25000,
      "engagement_rate": 0.25,
      "consistency": "high"
    },
    "multipliers": {
      "base_cpm": 27.5,
      "engagement": 1.3,
      "niche": 1.2,
      "consistency": 1.1
    },
    "final_cpm": 47.19,
    "estimated_total_price": 1179.75,
    "currency": "USD"
  },
  "iterations_used": 3,
  "message_history": []
}
```

**Notes:**
- This endpoint can take 10-30 seconds due to LLM processing
- Frontend should implement 45-second timeout
- Uses GPT-4o with MCP tool calling

---

### 4. Send Reply

```http
POST /send
```

**Description:** Sends the approved response and marks the thread as processed.

**Request Body:**
```json
{
  "thread_id": "thread_001",
  "content": "Hi Alex,\n\nThank you for..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Reply sent successfully",
  "thread_id": "thread_001",
  "sent_at": "2024-01-15T16:00:00Z"
}
```

---

## MCP Tools

The backend communicates with `mcp_server.py` via stdio. Available tools:

### Email Tools
| Tool | Description |
|------|-------------|
| `get_email_thread` | Fetch full thread by ID |
| `get_latest_emails` | List recent threads |
| `send_reply` | Send email response |
| `mark_as_processed` | Mark thread as handled |

### Brand Tools
| Tool | Description |
|------|-------------|
| `get_brand_context` | Get brand profile/guidelines |

### YouTube Tools
| Tool | Description |
|------|-------------|
| `fetch_channel_data` | Get channel stats (API + fallback) |
| `calculate_engagement` | Get engagement metrics |

### Pricing Tools
| Tool | Description |
|------|-------------|
| `calculate_offer_price` | Calculate fair CPM-based price |
| `validate_counter_offer` | Analyze counter-offer acceptability |

---

## Error Handling

All endpoints return consistent error format:

```json
{
  "success": false,
  "error": "Thread not found"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found
- `500` - Server Error

---

## CORS Configuration

Allowed origins:
- `http://localhost:3000`
- `http://localhost:5173`
- `http://localhost:5176`
- `http://127.0.0.1:*` (all ports)

---

## Rate Limits

Development mode has no rate limits. Production should implement:
- 60 requests/minute for list endpoints
- 10 requests/minute for generate endpoint (LLM calls)

---

*Last Updated: January 2026*
