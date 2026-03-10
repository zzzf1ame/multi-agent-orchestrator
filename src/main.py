"""
FastAPI application entry point for Multi-Agent Orchestrator.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from .api import router, ws_router
from .models.schemas import WebSocketMessage

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Multi-Agent Orchestrator")
    yield
    logger.info("Shutting down Multi-Agent Orchestrator")


# Create FastAPI application
app = FastAPI(
    title="Multi-Agent Orchestrator",
    description="Production-ready multi-agent system with LangGraph and FastAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)
app.include_router(ws_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic information."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multi-Agent Orchestrator</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .method { color: #007acc; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Multi-Agent Orchestrator</h1>
            <p>Production-ready multi-agent system built with Python, LangGraph, and FastAPI.</p>
            
            <h2>API Endpoints</h2>
            <div class="endpoint">
                <span class="method">GET</span> <code>/docs</code> - Interactive API documentation
            </div>
            <div class="endpoint">
                <span class="method">POST</span> <code>/api/v1/research</code> - Create research task
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <code>/api/v1/research/{task_id}</code> - Get task status
            </div>
            <div class="endpoint">
                <span class="method">WebSocket</span> <code>/ws/{client_id}</code> - Real-time updates
            </div>
            
            <h2>WebSocket Test</h2>
            <p><a href="/ws-test">Test WebSocket Connection</a></p>
            
            <h2>Features</h2>
            <ul>
                <li>Multi-agent workflow with Researcher and Writer agents</li>
                <li>LangGraph orchestration with state management</li>
                <li>Pydantic validation for structured data</li>
                <li>Real-time WebSocket communication</li>
                <li>Docker-ready deployment</li>
            </ul>
        </div>
    </body>
    </html>
    """


@app.get("/ws-test", response_class=HTMLResponse)
async def websocket_test():
    """WebSocket test page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test - Multi-Agent Orchestrator</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            #messages { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin: 10px 0; }
            .message { margin: 5px 0; padding: 5px; border-radius: 3px; }
            .sent { background-color: #e3f2fd; }
            .received { background-color: #f3e5f5; }
            .error { background-color: #ffebee; color: #c62828; }
            input, button { margin: 5px; padding: 8px; }
            button { background-color: #007acc; color: white; border: none; border-radius: 3px; cursor: pointer; }
            button:hover { background-color: #005a9e; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>WebSocket Test</h1>
            <div>
                <input type="text" id="clientId" placeholder="Client ID" value="test-client">
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
                <span id="status">Disconnected</span>
            </div>
            
            <div id="messages"></div>
            
            <div>
                <input type="text" id="taskId" placeholder="Task ID to subscribe">
                <button onclick="subscribe()">Subscribe</button>
                <button onclick="unsubscribe()">Unsubscribe</button>
            </div>
            
            <div>
                <button onclick="ping()">Ping</button>
                <button onclick="clearMessages()">Clear Messages</button>
            </div>
        </div>

        <script>
            let ws = null;
            let clientId = 'test-client';

            function addMessage(message, type = 'received') {
                const messages = document.getElementById('messages');
                const div = document.createElement('div');
                div.className = `message ${type}`;
                div.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong>: ${message}`;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }

            function connect() {
                clientId = document.getElementById('clientId').value || 'test-client';
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/${clientId}`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function(event) {
                    document.getElementById('status').textContent = 'Connected';
                    document.getElementById('status').style.color = 'green';
                    addMessage('Connected to WebSocket', 'sent');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addMessage(JSON.stringify(data, null, 2));
                };
                
                ws.onclose = function(event) {
                    document.getElementById('status').textContent = 'Disconnected';
                    document.getElementById('status').style.color = 'red';
                    addMessage('WebSocket connection closed', 'error');
                };
                
                ws.onerror = function(error) {
                    addMessage('WebSocket error: ' + error, 'error');
                };
            }

            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }

            function subscribe() {
                const taskId = document.getElementById('taskId').value;
                if (ws && taskId) {
                    const message = {
                        type: 'subscribe',
                        task_id: taskId
                    };
                    ws.send(JSON.stringify(message));
                    addMessage(`Subscribing to task: ${taskId}`, 'sent');
                }
            }

            function unsubscribe() {
                const taskId = document.getElementById('taskId').value;
                if (ws && taskId) {
                    const message = {
                        type: 'unsubscribe',
                        task_id: taskId
                    };
                    ws.send(JSON.stringify(message));
                    addMessage(`Unsubscribing from task: ${taskId}`, 'sent');
                }
            }

            function ping() {
                if (ws) {
                    const message = { type: 'ping' };
                    ws.send(JSON.stringify(message));
                    addMessage('Ping sent', 'sent');
                }
            }

            function clearMessages() {
                document.getElementById('messages').innerHTML = '';
            }
        </script>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "multi-agent-orchestrator",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )