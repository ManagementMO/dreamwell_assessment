"""
Dreamwell Influencer Agent - FastAPI Backend with MCP Client

CRITICAL: This is the FastAPI server that spawns mcp_server.py as a subprocess.
- Uses lifespan manager for MCP server lifecycle
- Stores MCP session in app.state.mcp_session
- All endpoints are async def
- CORS configured immediately after app creation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
import json
import logging

# MCP imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# OpenAI imports
from openai import AsyncOpenAI

# Configuration
import config

# Configure logging for FastAPI (can use stdout here)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


# ========== LIFESPAN MANAGER (CRITICAL) ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager that spawns mcp_server.py as subprocess on startup
    and cleans up on shutdown.
    
    The MCP session is stored in app.state.mcp_session and reused across
    all requests (NOT per-request).
    """
    logger.info("🚀 Starting FastAPI application...")
    
    # Configure subprocess parameters to spawn mcp_server.py
    import sys
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
        env=None  # Subprocess will load .env itself (Rule 7)
    )
    
    # Spawn MCP server as subprocess and establish stdio connection
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the MCP session
            await session.initialize()
            
            # Store session in app.state for reuse across all requests
            app.state.mcp_session = session
            
            logger.info("✅ MCP server started and session initialized")
            logger.info(f"✅ MCP session stored in app.state.mcp_session")
            
            # List available tools for debugging
            try:
                tools_list = await session.list_tools()
                tool_names = [tool.name for tool in tools_list.tools]
                logger.info(f"📋 Available MCP tools: {tool_names}")
            except Exception as e:
                logger.error(f"Failed to list MCP tools: {e}")
            
            # Server runs here - yield control to FastAPI
            yield
            
            # Cleanup on shutdown (automatic via context managers)
            logger.info("🛑 Shutting down MCP server...")


# ========== FASTAPI APP INITIALIZATION ==========

app = FastAPI(
    title="Dreamwell Influencer Agent API",
    description="AI agent system for automating influencer email responses",
    version="1.0.0",
    lifespan=lifespan  # CRITICAL: Attach lifespan manager
)

# ⚠️ CRITICAL: Configure CORS immediately after app creation (Rule 5)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("✅ CORS middleware configured")


# ========== HELPER FUNCTIONS ==========

def mcp_tool_to_openai_schema(mcp_tool) -> Dict[str, Any]:
    """
    Convert an MCP tool to OpenAI function schema.
    
    MCP tools use JSON Schema for inputSchema, which is compatible with
    OpenAI's function calling format.
    """
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description,
            "parameters": mcp_tool.inputSchema  # Already in JSON Schema format
        }
    }


async def convert_mcp_tools_to_openai_schema(session: ClientSession) -> list:
    """
    Get all MCP tools from the server and convert them to OpenAI format.
    """
    tools_list = await session.list_tools()
    openai_tools = [mcp_tool_to_openai_schema(tool) for tool in tools_list.tools]
    logger.info(f"Converted {len(openai_tools)} MCP tools to OpenAI schema")
    return openai_tools


# ========== AGENT ORCHESTRATOR (ReAct Loop - Day 2) ==========

async def agent_orchestrator(email_context: Dict[str, Any], brand_id: str) -> Dict[str, Any]:
    """
    Agent Orchestrator using ReAct Loop Pattern.
    
    1. Converts MCP tools to OpenAI schema
    2. Enters reasoning loop (max 5 iterations)
    3. Calls LLM with message history
    4. Executes chosen tools via MCP
    5. Returns final response
    """
    session = app.state.mcp_session
    openai_tools = await convert_mcp_tools_to_openai_schema(session)
    
    # System Prompt
    system_prompt = f"""You are an expert influencer marketing manager for {brand_id}.
    Your goal is to analyze the email and generate a professional response.
    
    MANDATORY TOOL CALLS (you MUST call these in order):
    1. fetch_channel_data - Get the influencer's YouTube metrics
    2. get_brand_context - Get budget and guidelines for {brand_id}
    3. calculate_offer_price - ALWAYS calculate fair CPM-based price (REQUIRED!)
    4. validate_counter_offer - If they proposed a price, validate it
    
    You MUST call calculate_offer_price before drafting any response. This is required for the UI to display pricing.
    
    CRITICAL OUTPUT FORMAT:
    After calling all required tools, output ONLY the email itself.
    DO NOT include any analysis, commentary, or explanation.
    
    Your final output must be EXACTLY in this format:
    
    Subject: [email subject line]
    
    [email body content]
    
    [signature]
    
    NO other text. NO preamble. NO bullet points. NO questions.
    JUST the email that would be sent to the influencer."""

    # Initialize Message History
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Email Context: {json.dumps(email_context)}"}
    ]
    
    MAX_ITERATIONS = 5
    pricing_breakdown = None
    
    logger.info(f"🤖 Starting Agent Loop for {brand_id} (Max {MAX_ITERATIONS} iterations)")
    
    for i in range(MAX_ITERATIONS):
        logger.info(f"🔄 Iteration {i+1}/{MAX_ITERATIONS}")
        
        # 1. Call LLM
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=openai_tools,
            tool_choice="auto"
        )
        
        assistant_msg = response.choices[0].message
        messages.append(assistant_msg)
        
        # 2. Check for Tool Calls
        if not assistant_msg.tool_calls:
            logger.info("✅ Agent finished reasoning (no more tool calls)")
            break
            
        # 3. Execute Tools
        for tool_call in assistant_msg.tool_calls:
            try:
                t_name = tool_call.function.name
                t_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"🛠️ Agent calling: {t_name}({t_args})")
                
                # Execute via MCP
                result = await session.call_tool(t_name, t_args)
                
                # Capture pricing data if available (for UI)
                if t_name == "calculate_offer_price" and hasattr(result, 'content'):
                     # MCP returns content list, need to parse
                     pass 
                
                # Parse MCP result to string/dict for LLM
                # MCP results come as objects with 'content', 'isError'
                tool_output = "Error executing tool"
                if hasattr(result, 'content') and len(result.content) > 0:
                     if hasattr(result.content[0], 'text'):
                         tool_output = result.content[0].text
                         
                         # Capture pricing breakdown from tool output for UI
                         if t_name == "calculate_offer_price":
                             try:
                                 data = json.loads(tool_output)
                                 if data.get("success"):
                                     calc = data.get("calculation", {})
                                     mults = calc.get("multipliers", {})
                                     rec = data.get("recommendation", {})
                                     # Map to flat structure frontend expects
                                     pricing_breakdown = {
                                         "recommended_offer": rec.get("offer_price", calc.get("estimated_total_price", 0)),
                                         "engagement_multiplier": mults.get("engagement", 1.0),
                                         "niche_multiplier": mults.get("niche", 1.0),
                                         "consistency_multiplier": mults.get("consistency", 1.0),
                                         "base_cpm": mults.get("base_cpm", 10),
                                         "final_cpm": calc.get("final_cpm", 10),
                                         "metrics": calc.get("metrics", {}),
                                     }
                             except:
                                 pass
                     else:
                         tool_output = str(result.content[0])
                else:
                    tool_output = str(result)
                
                logger.info(f"📤 Tool Output: {tool_output[:200]}...") # Log partial output
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output
                })
                
            except Exception as e:
                logger.error(f"❌ Tool Execution Error: {e}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f"Error: {str(e)}"
                })

    # Default category derivation (simple)
    category = "response"
    last_content = messages[-1].content
    if last_content:
        lower_content = last_content.lower()
        if "negotiat" in lower_content: category = "negotiation"
        elif "accept" in lower_content: category = "acceptance"
        elif "decline" in lower_content: category = "rejection"
    
    return {
        "category": category,
        "response_draft": messages[-1].content,
        "pricing_breakdown": pricing_breakdown,
        "iterations_used": i + 1,
        "message_history": [] # Don't return full history to frontend yet to save bandwidth
    }


# ========== REST API ENDPOINTS ==========

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Dreamwell Influencer Agent API",
        "version": "1.0.0"
    }


@app.get("/api/emails")
async def list_emails(limit: int = 20):
    """
    List recent email threads via MCP tool.
    
    Args:
        limit: Maximum number of emails to return (default: 20)
    
    Returns:
        List of email summaries
    """
    logger.info(f"GET /api/emails called with limit={limit}")
    
    try:
        session = app.state.mcp_session
        
        # Call MCP tool (async!)
        result = await session.call_tool("get_latest_emails", {"limit": limit})
        
        logger.info(f"MCP tool returned: {result}")
        
        # Extract content from MCP result
        if hasattr(result, 'content') and len(result.content) > 0:
            # MCP returns results in content array
            content_item = result.content[0]
            if hasattr(content_item, 'text'):
                data = json.loads(content_item.text)
                return data
        
        # Fallback if format is different
        return result
        
    except Exception as e:
        logger.error(f"Error listing emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/emails/{thread_id}")
async def get_email_thread(thread_id: str):
    """
    Get full email thread by ID via MCP tool.
    
    Args:
        thread_id: The thread identifier
    
    Returns:
        Complete email thread with all messages
    """
    logger.info(f"GET /api/emails/{thread_id} called")
    
    try:
        session = app.state.mcp_session
        
        # Call MCP tool (async!)
        result = await session.call_tool("get_email_thread", {"thread_id": thread_id})
        
        logger.info(f"MCP tool returned: {result}")
        
        # Extract content from MCP result
        if hasattr(result, 'content') and len(result.content) > 0:
            content_item = result.content[0]
            if hasattr(content_item, 'text'):
                data = json.loads(content_item.text)
                if not data.get("success"):
                    raise HTTPException(status_code=404, detail=data.get("error"))
                
                # Map 'thread' to 'messages' for frontend compatibility
                email_data = data.get("data", {})
                if "thread" in email_data and "messages" not in email_data:
                    email_data["messages"] = email_data["thread"]
                
                # Also extract subject from first message if not present
                if not email_data.get("subject") and email_data.get("messages"):
                    email_data["subject"] = email_data["messages"][0].get("subject", "No Subject")
                
                return {"success": True, "data": email_data}
        
        # Fallback
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
async def generate_response(request: Dict[str, Any]):
    """
    PLACEHOLDER: Generate AI response for an email.
    
    This endpoint will be fully implemented in Day 2 with the ReAct Loop.
    For now, it returns a simple placeholder response.
    
    Expected request body:
    {
        "thread_id": "string",
        "brand_id": "string" (optional, defaults to "perplexity")
    }
    
    Returns:
        Generated response with category, draft, and metadata
    """
    logger.info(f"POST /api/generate called with request: {request}")
    
    try:
        thread_id = request.get("thread_id")
        brand_id = request.get("brand_id", "perplexity")
        
        if not thread_id:
            raise HTTPException(status_code=400, detail="thread_id is required")
        
        # Get email thread
        session = app.state.mcp_session
        email_result = await session.call_tool("get_email_thread", {"thread_id": thread_id})
        
        # Extract email data
        if hasattr(email_result, 'content') and len(email_result.content) > 0:
            content_item = email_result.content[0]
            if hasattr(content_item, 'text'):
                email_data = json.loads(content_item.text)
                if not email_data.get("success"):
                    raise HTTPException(status_code=404, detail=email_data.get("error"))
                email_context = email_data.get("data")
            else:
                email_context = email_result
        else:
            email_context = email_result
        
        # Call agent orchestrator (placeholder for Day 1)
        result = await agent_orchestrator(email_context, brand_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send")
async def send_reply_endpoint(request: Dict[str, Any]):
    """
    Send/approve a response to an email thread.
    
    Expected request body:
    {
        "thread_id": "string",
        "content": "string"
    }
    
    Returns:
        Confirmation of email sent
    """
    logger.info(f"POST /api/send called")
    
    try:
        thread_id = request.get("thread_id")
        content = request.get("content")
        
        if not thread_id or not content:
            raise HTTPException(status_code=400, detail="thread_id and content are required")
        
        session = app.state.mcp_session
        
        # Send reply via MCP tool
        send_result = await session.call_tool("send_reply", {
            "thread_id": thread_id,
            "content": content
        })
        
        # Mark as processed
        mark_result = await session.call_tool("mark_as_processed", {
            "thread_id": thread_id
        })
        
        # Extract results
        if hasattr(send_result, 'content') and len(send_result.content) > 0:
            content_item = send_result.content[0]
            if hasattr(content_item, 'text'):
                data = json.loads(content_item.text)
                return data
        
        return send_result
        
    except Exception as e:
        logger.error(f"Error sending reply: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== MAIN ENTRY POINT ==========

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {config.FASTAPI_HOST}:{config.FASTAPI_PORT}")
    
    uvicorn.run(
        "backend_main:app",
        host=config.FASTAPI_HOST,
        port=config.FASTAPI_PORT,
        reload=True,
        log_level="info"
    )

