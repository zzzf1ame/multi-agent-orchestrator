"""
Tests for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
import json

from src.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """Test cases for API endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Multi-Agent Orchestrator" in response.text
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_api_health_check(self):
        """Test API health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "active_tasks" in data
        assert "total_tasks" in data
    
    def test_create_research_task(self):
        """Test research task creation."""
        payload = {
            "topic": "Machine Learning trends in 2024",
            "depth": "detailed",
            "max_sources": 5
        }
        
        response = client.post("/api/v1/research", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert "message" in data
        assert "created_at" in data
    
    def test_create_research_task_validation(self):
        """Test research task creation with invalid data."""
        # Missing required field
        payload = {
            "depth": "detailed"
        }
        
        response = client.post("/api/v1/research", json=payload)
        assert response.status_code == 422
    
    def test_get_research_task_not_found(self):
        """Test getting non-existent research task."""
        response = client.get("/api/v1/research/nonexistent_task")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Task not found"
    
    def test_list_research_tasks(self):
        """Test listing research tasks."""
        response = client.get("/api/v1/research")
        assert response.status_code == 200
        
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "filtered" in data
        assert isinstance(data["tasks"], list)
    
    def test_websocket_test_page(self):
        """Test WebSocket test page."""
        response = client.get("/ws-test")
        assert response.status_code == 200
        assert "WebSocket Test" in response.text
        assert "connect()" in response.text


class TestWebSocketConnection:
    """Test cases for WebSocket connections."""
    
    def test_websocket_connection(self):
        """Test WebSocket connection."""
        with client.websocket_connect("/ws/test-client") as websocket:
            # Should receive welcome message
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == "connection"
            assert "test-client" in message["message"]
            assert message["data"]["client_id"] == "test-client"
    
    def test_websocket_ping_pong(self):
        """Test WebSocket ping-pong."""
        with client.websocket_connect("/ws/test-client") as websocket:
            # Receive welcome message
            websocket.receive_text()
            
            # Send ping
            ping_message = {"type": "ping"}
            websocket.send_text(json.dumps(ping_message))
            
            # Receive pong
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == "pong"
            assert "Connection alive" in message["message"]
    
    def test_websocket_subscribe(self):
        """Test WebSocket task subscription."""
        with client.websocket_connect("/ws/test-client") as websocket:
            # Receive welcome message
            websocket.receive_text()
            
            # Subscribe to task
            subscribe_message = {
                "type": "subscribe",
                "task_id": "test_task_123"
            }
            websocket.send_text(json.dumps(subscribe_message))
            
            # Receive subscription confirmation
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == "subscription"
            assert message["task_id"] == "test_task_123"
            assert "Subscribed" in message["message"]
    
    def test_websocket_invalid_message(self):
        """Test WebSocket with invalid message."""
        with client.websocket_connect("/ws/test-client") as websocket:
            # Receive welcome message
            websocket.receive_text()
            
            # Send invalid JSON
            websocket.send_text("invalid json")
            
            # Receive error message
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == "error"
            assert "Invalid JSON" in message["message"]


class TestAPIValidation:
    """Test cases for API validation."""
    
    def test_research_request_validation(self):
        """Test research request validation."""
        # Topic too short
        payload = {"topic": "AI", "depth": "detailed"}
        response = client.post("/api/v1/research", json=payload)
        assert response.status_code == 422
        
        # Invalid depth
        payload = {"topic": "Valid topic here", "depth": "invalid_depth"}
        response = client.post("/api/v1/research", json=payload)
        assert response.status_code == 422
        
        # Max sources out of range
        payload = {
            "topic": "Valid topic here",
            "depth": "detailed",
            "max_sources": 25
        }
        response = client.post("/api/v1/research", json=payload)
        assert response.status_code == 422
    
    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = client.options("/api/v1/research")
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers