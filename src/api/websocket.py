"""
WebSocket handlers for real-time communication.
"""
import logging
import json
from typing import Dict, Set
import asyncio
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

from ..models.schemas import WebSocketMessage, TaskStatus

logger = logging.getLogger(__name__)

# WebSocket router
ws_router = APIRouter()

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}
client_subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of task_ids


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        logger.info(f"Client {client_id} connected")
        
        # Send welcome message
        welcome_msg = WebSocketMessage(
            type="connection",
            message=f"Connected as client {client_id}",
            data={"client_id": client_id}
        )
        await self.send_personal_message(welcome_msg.dict(), client_id)
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_to_subscribers(self, message: dict, task_id: str):
        """Broadcast message to all clients subscribed to a task."""
        for client_id, subscriptions in self.client_subscriptions.items():
            if task_id in subscriptions:
                await self.send_personal_message(message, client_id)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected clients."""
        for client_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, client_id)
    
    def subscribe_to_task(self, client_id: str, task_id: str):
        """Subscribe client to task updates."""
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].add(task_id)
            logger.info(f"Client {client_id} subscribed to task {task_id}")
    
    def unsubscribe_from_task(self, client_id: str, task_id: str):
        """Unsubscribe client from task updates."""
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].discard(task_id)
            logger.info(f"Client {client_id} unsubscribed from task {task_id}")
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()


@ws_router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time communication.
    
    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_client_message(message, client_id)
            except json.JSONDecodeError:
                error_msg = WebSocketMessage(
                    type="error",
                    message="Invalid JSON format"
                )
                await manager.send_personal_message(error_msg.dict(), client_id)
            except Exception as e:
                logger.error(f"Error handling message from {client_id}: {e}")
                error_msg = WebSocketMessage(
                    type="error",
                    message=f"Error processing message: {str(e)}"
                )
                await manager.send_personal_message(error_msg.dict(), client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)


async def handle_client_message(message: dict, client_id: str):
    """
    Handle incoming client messages.
    
    Args:
        message: Client message
        client_id: Client identifier
    """
    message_type = message.get("type")
    
    if message_type == "subscribe":
        # Subscribe to task updates
        task_id = message.get("task_id")
        if task_id:
            manager.subscribe_to_task(client_id, task_id)
            response = WebSocketMessage(
                type="subscription",
                task_id=task_id,
                message=f"Subscribed to task {task_id}"
            )
            await manager.send_personal_message(response.dict(), client_id)
    
    elif message_type == "unsubscribe":
        # Unsubscribe from task updates
        task_id = message.get("task_id")
        if task_id:
            manager.unsubscribe_from_task(client_id, task_id)
            response = WebSocketMessage(
                type="subscription",
                task_id=task_id,
                message=f"Unsubscribed from task {task_id}"
            )
            await manager.send_personal_message(response.dict(), client_id)
    
    elif message_type == "ping":
        # Respond to ping with pong
        response = WebSocketMessage(
            type="pong",
            message="Connection alive"
        )
        await manager.send_personal_message(response.dict(), client_id)
    
    else:
        # Unknown message type
        response = WebSocketMessage(
            type="error",
            message=f"Unknown message type: {message_type}"
        )
        await manager.send_personal_message(response.dict(), client_id)


async def notify_task_update(
    task_id: str,
    status: TaskStatus,
    message: str,
    data: dict = None
):
    """
    Notify subscribers about task updates.
    
    Args:
        task_id: Task identifier
        status: Current task status
        message: Update message
        data: Additional data
    """
    update_msg = WebSocketMessage(
        type="task_update",
        task_id=task_id,
        status=status,
        message=message,
        data=data or {}
    )
    
    await manager.broadcast_to_subscribers(update_msg.dict(), task_id)


async def notify_workflow_progress(
    task_id: str,
    step: str,
    progress: int,
    details: str = None
):
    """
    Notify about workflow progress.
    
    Args:
        task_id: Task identifier
        step: Current workflow step
        progress: Progress percentage (0-100)
        details: Additional details
    """
    progress_msg = WebSocketMessage(
        type="progress",
        task_id=task_id,
        message=f"Step: {step}",
        data={
            "step": step,
            "progress": progress,
            "details": details
        }
    )
    
    await manager.broadcast_to_subscribers(progress_msg.dict(), task_id)


# Utility function to get connection manager
def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager