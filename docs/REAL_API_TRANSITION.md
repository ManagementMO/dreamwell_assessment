# Moving to Production: Real API Transition Guide

This guide details the specific changes required to switch the Dreamwell Agent from "Mock Mode" (using JSON fixtures) to "Real API Mode" (using live YouTube and Gmail data).

---

## 1. YouTube Data API (Full Implementation)

Currently, the system uses a hybrid approach: it verifies the channel exists via API but falls back to local data for engagement metrics.

### Step A: Enable API Key
Ensure your `.env` file has a valid key:
```bash
YOUTUBE_API_KEY=AIzaSy...
```

### Step B: Implement Real Engagement Calculation
Modify `mcp_server.py` to fetch recent videos and calculate real rates instead of using stored values.

**Code Change in `mcp_server.py`:**

```python
@mcp.tool()
def calculate_engagement(channel_id: str) -> Dict[str, Any]:
    """Calculate engagement from last 10 videos via Real API"""
    
    if not YOUTUBE_API_KEY:
        # Fallback to existing mock logic
        return _use_mock_engagement(channel_id)

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        
        # 1. Fetch last 10 videos
        search_resp = youtube.search().list(
            channelId=channel_id,
            type="video",
            order="date",
            part="id",
            maxResults=10
        ).execute()
        
        video_ids = [item['id']['videoId'] for item in search_resp.get('items', [])]
        
        if not video_ids:
            return {"engagement_rate": 0.0, "avg_views": 0}

        # 2. Get statistics for these videos
        stats_resp = youtube.videos().list(
            id=','.join(video_ids),
            part="statistics"
        ).execute()
        
        total_views = 0
        total_interactions = 0
        valid_videos = 0

        for item in stats_resp.get('items', []):
            stats = item['statistics']
            views = int(stats.get('viewCount', 0))
            likes = int(stats.get('likeCount', 0))
            comments = int(stats.get('commentCount', 0))
            
            if views > 0:
                total_views += views
                total_interactions += (likes + comments)
                valid_videos += 1

        if valid_videos == 0:
            return {"engagement_rate": 0.0, "avg_views": 0}

        # 3. Calculate metrics
        avg_views = total_views / valid_videos
        engagement_rate = (total_interactions / total_views) if total_views > 0 else 0

        return {
            "success": True,
            "engagement_rate": round(engagement_rate, 4),
            "avg_views": int(avg_views),
            "consistency_score": "high" # Logic needed: check interval between 'publishedAt'
        }

    except Exception as e:
        logger.error(f"YouTube API Error: {e}")
        return {"success": False, "error": str(e)}
```

---

## 2. Gmail Integration (Replacing JSON Fixtures)

Currently, email tools read from `data/email_fixtures.json`. You need to replace this with the Gmail API.

### Step A: Authentication Setup
1. Create a Project in Google Cloud Console.
2. Enable **Gmail API**.
3. Create OAuth 2.0 Credentials (download `credentials.json`).
4. Install auth library: `pip install google-auth-oauthlib google-auth-httplib2`

### Step B: Helper Class
Add this to `mcp_server.py`:

```python
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    """Authenticate and return Gmail service"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Requires interactive login on first run
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build('gmail', 'v1', credentials=creds)
```

### Step C: Update Email Tools

**1. `get_latest_emails` replacement:**
```python
@mcp.tool()
def get_latest_emails(limit: int = 10) -> Dict[str, Any]:
    service = get_gmail_service()
    
    # List threads
    results = service.users().threads().list(
        userId='me', maxResults=limit
    ).execute()
    threads = results.get('threads', [])

    summary_list = []
    for t in threads:
        # Fetch minimal details for list view
        t_data = service.users().threads().get(
            userId='me', id=t['id'], format='metadata'
        ).execute()
        
        # Parse headers (Subject, From) from t_data...
        # Add to summary_list...
        
    return {"success": True, "data": summary_list}
```

**2. `send_reply` replacement:**
```python
@mcp.tool()
def send_reply(thread_id: str, content: str) -> Dict[str, Any]:
    service = get_gmail_service()
    
    # Construct MIME message
    from email.mime.text import MIMEText
    import base64
    
    message = MIMEText(content)
    message['to'] = "influencer@example.com" # Extract from thread
    message['subject'] = "Re: Partnership"    # Extract from thread
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    sent = service.users().messages().send(
        userId='me', body={'raw': raw, 'threadId': thread_id}
    ).execute()
    
    return {"success": True, "id": sent['id']}
```

---

## 3. Brand Context (Database)

Replace `data/brand_profiles.json` with a database fetch.

**Likely Stack:** PostgreSQL + SQLAlchemy / Prisma

```python
# mcp_server.py

def get_brand_context(brand_id: str):
    # Old: return brands.get(brand_id)
    
    # New: Connect to DB
    import psycopg2
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("SELECT context, guidelines FROM brands WHERE id = %s", (brand_id,))
    result = cur.fetchone()
    return result
```
