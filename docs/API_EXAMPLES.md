# 📚 API Examples & Usage Guide

## Complete API Usage Examples

### 1. Creating a Research Task

#### Request
```bash
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Quantum Computing applications in cryptography",
    "depth": "comprehensive",
    "max_sources": 8
  }'
```

#### Response
```json
{
  "task_id": "task_f7a8b9c0",
  "status": "pending",
  "message": "Research task created for topic: Quantum Computing applications in cryptography",
  "created_at": "2024-03-10T15:45:30.123456Z"
}
```

### 2. Monitoring Task Progress

#### WebSocket Connection
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/client-123');

// Subscribe to task updates
ws.send(JSON.stringify({
  type: 'subscribe',
  task_id: 'task_f7a8b9c0'
}));

// Receive real-time updates
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Task Update:', update);
};
```

#### Sample WebSocket Messages
```json
// Task started
{
  "type": "task_update",
  "task_id": "task_f7a8b9c0",
  "status": "researching",
  "message": "Researcher agent initiated information gathering",
  "data": {
    "progress": 10,
    "current_step": "initialization"
  },
  "timestamp": "2024-03-10T15:45:31.000000Z"
}

// Research progress
{
  "type": "progress",
  "task_id": "task_f7a8b9c0",
  "message": "Step: source_analysis",
  "data": {
    "step": "source_analysis",
    "progress": 45,
    "details": "Analyzing quantum cryptography research papers",
    "sources_processed": 3,
    "total_sources": 8
  },
  "timestamp": "2024-03-10T15:46:15.000000Z"
}

// Validation phase
{
  "type": "task_update",
  "task_id": "task_f7a8b9c0",
  "status": "writing",
  "message": "Research validated successfully, Writer agent starting article generation",
  "data": {
    "progress": 70,
    "validation_score": 0.94
  },
  "timestamp": "2024-03-10T15:47:22.000000Z"
}

// Task completed
{
  "type": "task_update",
  "task_id": "task_f7a8b9c0",
  "status": "completed",
  "message": "Article generation completed successfully",
  "data": {
    "progress": 100,
    "word_count": 2341,
    "sections_generated": 6
  },
  "timestamp": "2024-03-10T15:48:45.000000Z"
}
```

### 3. Retrieving Complete Results

#### Request
```bash
curl -X GET "http://localhost:8000/api/v1/research/task_f7a8b9c0"
```

#### Response
```json
{
  "task_id": "task_f7a8b9c0",
  "status": "completed",
  "research": {
    "topic": "Quantum Computing applications in cryptography",
    "summary": "Quantum computing represents a paradigm shift in computational capabilities with profound implications for cryptographic systems. Current research focuses on both the threats quantum computers pose to existing encryption methods and the opportunities they create for quantum-resistant cryptographic protocols. Post-quantum cryptography development is accelerating as organizations prepare for the quantum era.",
    "key_findings": [
      "Shor's algorithm threatens RSA and elliptic curve cryptography within 10-15 years",
      "NIST has standardized post-quantum cryptographic algorithms including CRYSTALS-Kyber",
      "Quantum key distribution (QKD) offers theoretically unbreakable communication channels",
      "Hybrid classical-quantum cryptographic systems are emerging as transition solutions",
      "Major tech companies are investing billions in quantum-safe infrastructure",
      "Government agencies are mandating quantum-readiness assessments",
      "Quantum random number generators provide enhanced entropy for cryptographic keys",
      "Lattice-based cryptography shows promise for post-quantum security"
    ],
    "sources": [
      {
        "title": "NIST Post-Quantum Cryptography Standards",
        "url": "https://csrc.nist.gov/projects/post-quantum-cryptography",
        "type": "government_standard",
        "date": "2024"
      },
      {
        "title": "Quantum Supremacy and Cryptographic Implications",
        "url": "https://example.com/quantum-crypto-research",
        "type": "academic_paper",
        "date": "2024"
      },
      {
        "title": "Industry Report: Quantum Computing Market Analysis",
        "url": "https://example.com/quantum-market-2024",
        "type": "industry_report",
        "date": "2024"
      }
    ],
    "metadata": {
      "depth": "comprehensive",
      "agent": "Researcher",
      "confidence_score": 0.94,
      "processing_time_ms": 3247,
      "sources_analyzed": 8,
      "validation_passed": true
    },
    "timestamp": "2024-03-10T15:47:18.987654Z"
  },
  "article": {
    "title": "Quantum Computing Revolution: Transforming Cryptographic Security in the Digital Age",
    "content": "## Executive Summary\n\nQuantum computing represents a paradigm shift in computational capabilities with profound implications for cryptographic systems...\n\n## Key Findings\n\n### 1. Immediate Threats to Current Cryptography\nShor's algorithm, when implemented on sufficiently powerful quantum computers, threatens the foundation of modern public-key cryptography...\n\n### 2. Post-Quantum Cryptographic Solutions\nThe National Institute of Standards and Technology (NIST) has recently standardized several post-quantum cryptographic algorithms...\n\n### 3. Quantum Key Distribution Opportunities\nQuantum key distribution (QKD) leverages the principles of quantum mechanics to create theoretically unbreakable communication channels...\n\n## Detailed Analysis\n\n### Current State of Quantum Computing\nMajor technology companies including IBM, Google, and Microsoft have made significant strides in quantum computing development...\n\n### Cryptographic Vulnerabilities\nThe advent of practical quantum computers poses existential threats to widely-used cryptographic protocols...\n\n### Transition Strategies\nOrganizations must begin preparing for the post-quantum era through comprehensive quantum-readiness assessments...\n\n## Implications\n\nThe research findings on quantum computing applications in cryptography have several critical implications:\n\n- **Immediate Action Required**: Organizations must begin quantum-readiness assessments now\n- **Investment Priorities**: Significant resources needed for cryptographic infrastructure updates\n- **Regulatory Compliance**: Government mandates for quantum-safe systems are emerging\n- **Competitive Advantage**: Early adoption of quantum-resistant technologies provides market benefits\n\n## Conclusion\n\nThe intersection of quantum computing and cryptography represents one of the most significant technological challenges and opportunities of our time. While quantum computers threaten existing cryptographic systems, they also enable new forms of ultra-secure communication through quantum cryptographic protocols.\n\nOrganizations must act decisively to assess their quantum readiness, implement post-quantum cryptographic solutions, and develop comprehensive transition strategies. The quantum era is not a distant future concern—it is an immediate strategic imperative that requires attention today.\n\n## References\n\n1. NIST Post-Quantum Cryptography Standards - https://csrc.nist.gov/projects/post-quantum-cryptography\n2. Quantum Supremacy and Cryptographic Implications - https://example.com/quantum-crypto-research\n3. Industry Report: Quantum Computing Market Analysis - https://example.com/quantum-market-2024",
    "word_count": 2341,
    "sections": [
      "Executive Summary",
      "Key Findings",
      "Detailed Analysis", 
      "Implications",
      "Conclusion"
    ],
    "research_reference": "task_f7a8b9c0",
    "timestamp": "2024-03-10T15:48:45.123456Z"
  },
  "started_at": "2024-03-10T15:45:30.123456Z",
  "completed_at": "2024-03-10T15:48:45.123456Z",
  "duration_seconds": 195.0,
  "error": null
}
```

### 4. Error Handling Examples

#### Validation Error Response
```json
{
  "detail": [
    {
      "loc": ["body", "topic"],
      "msg": "ensure this value has at least 3 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 3}
    }
  ]
}
```

#### Task Failure Response
```json
{
  "task_id": "task_error123",
  "status": "failed",
  "research": null,
  "article": null,
  "error": "Research validation failed: Insufficient key findings",
  "started_at": "2024-03-10T15:45:30.123456Z",
  "completed_at": "2024-03-10T15:46:15.123456Z",
  "duration_seconds": 45.0
}
```

## Python Client Example

```python
import asyncio
import aiohttp
import websockets
import json

class MultiAgentClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
    
    async def create_research_task(self, topic, depth="detailed", max_sources=5):
        """Create a new research task."""
        async with aiohttp.ClientSession() as session:
            payload = {
                "topic": topic,
                "depth": depth,
                "max_sources": max_sources
            }
            
            async with session.post(
                f"{self.base_url}/api/v1/research",
                json=payload
            ) as response:
                return await response.json()
    
    async def get_task_result(self, task_id):
        """Get task result by ID."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v1/research/{task_id}"
            ) as response:
                return await response.json()
    
    async def monitor_task_progress(self, task_id, client_id="python-client"):
        """Monitor task progress via WebSocket."""
        uri = f"{self.ws_url}/ws/{client_id}"
        
        async with websockets.connect(uri) as websocket:
            # Subscribe to task updates
            subscribe_msg = {
                "type": "subscribe",
                "task_id": task_id
            }
            await websocket.send(json.dumps(subscribe_msg))
            
            # Listen for updates
            async for message in websocket:
                data = json.loads(message)
                print(f"Update: {data}")
                
                if data.get("status") == "completed":
                    break

# Usage example
async def main():
    client = MultiAgentClient()
    
    # Create research task
    task = await client.create_research_task(
        topic="Machine Learning in Healthcare",
        depth="comprehensive",
        max_sources=6
    )
    
    task_id = task["task_id"]
    print(f"Created task: {task_id}")
    
    # Monitor progress
    await client.monitor_task_progress(task_id)
    
    # Get final result
    result = await client.get_task_result(task_id)
    print(f"Final result: {result['status']}")
    print(f"Article word count: {result['article']['word_count']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## JavaScript/Node.js Client Example

```javascript
const axios = require('axios');
const WebSocket = require('ws');

class MultiAgentClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.wsUrl = baseUrl.replace('http', 'ws');
    }
    
    async createResearchTask(topic, depth = 'detailed', maxSources = 5) {
        try {
            const response = await axios.post(`${this.baseUrl}/api/v1/research`, {
                topic,
                depth,
                max_sources: maxSources
            });
            return response.data;
        } catch (error) {
            console.error('Error creating task:', error.response?.data || error.message);
            throw error;
        }
    }
    
    async getTaskResult(taskId) {
        try {
            const response = await axios.get(`${this.baseUrl}/api/v1/research/${taskId}`);
            return response.data;
        } catch (error) {
            console.error('Error getting task result:', error.response?.data || error.message);
            throw error;
        }
    }
    
    monitorTaskProgress(taskId, clientId = 'js-client') {
        return new Promise((resolve, reject) => {
            const ws = new WebSocket(`${this.wsUrl}/ws/${clientId}`);
            
            ws.on('open', () => {
                // Subscribe to task updates
                ws.send(JSON.stringify({
                    type: 'subscribe',
                    task_id: taskId
                }));
            });
            
            ws.on('message', (data) => {
                const message = JSON.parse(data.toString());
                console.log('Update:', message);
                
                if (message.status === 'completed' || message.status === 'failed') {
                    ws.close();
                    resolve(message);
                }
            });
            
            ws.on('error', (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            });
        });
    }
}

// Usage example
async function main() {
    const client = new MultiAgentClient();
    
    try {
        // Create research task
        const task = await client.createResearchTask(
            'Blockchain technology in supply chain management',
            'comprehensive',
            7
        );
        
        console.log(`Created task: ${task.task_id}`);
        
        // Monitor progress
        await client.monitorTaskProgress(task.task_id);
        
        // Get final result
        const result = await client.getTaskResult(task.task_id);
        console.log(`Final status: ${result.status}`);
        console.log(`Article sections: ${result.article.sections.length}`);
        
    } catch (error) {
        console.error('Error:', error);
    }
}

main();
```

## Rate Limiting & Best Practices

### Rate Limits
- **API Endpoints**: 10 requests/second per IP
- **WebSocket Connections**: 5 connections/second per IP
- **Task Creation**: 5 tasks/minute per IP

### Best Practices
1. **Use WebSocket for Real-time Updates**: More efficient than polling
2. **Handle Errors Gracefully**: Implement retry logic with exponential backoff
3. **Validate Input**: Check data before sending to API
4. **Monitor Task Status**: Don't assume tasks will always succeed
5. **Cleanup Resources**: Close WebSocket connections when done