# FixFeeder API Documentation

This document provides comprehensive API reference for FixFeeder's REST API and monitoring endpoints.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URLs](#base-urls)
- [REST API Endpoints](#rest-api-endpoints)
- [Metrics Endpoints](#metrics-endpoints)
- [WebSocket API](#websocket-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Overview

FixFeeder provides multiple API interfaces for accessing message data, system metrics, and configuration:

- **REST API**: HTTP-based access to message data and system information
- **Metrics API**: Prometheus-compatible metrics endpoint
- **Dashboard API**: Web interface for real-time monitoring
- **WebSocket API**: Real-time message streaming (future enhancement)

## Authentication

Currently, FixFeeder operates without authentication for development environments. For production deployments, implement authentication via:

- **API Keys**: Header-based authentication
- **JWT Tokens**: Stateless authentication
- **OAuth 2.0**: Integration with identity providers

```http
# Future authentication header
Authorization: Bearer <jwt_token>
# or
X-API-Key: <api_key>
```

## Base URLs

| Environment | Base URL | Description |
|-------------|----------|-------------|
| Development | http://localhost:5001 | Local development |
| Production | https://fixfeeder.company.com | Production deployment |
| Metrics | http://localhost:8000 | Prometheus metrics |

## REST API Endpoints

### Messages API

#### Get Recent Messages

Retrieve the most recent FIX messages with optional filtering.

```http
GET /api/messages
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Maximum number of messages to return (1-1000) |
| `offset` | integer | 0 | Number of messages to skip for pagination |
| `symbol` | string | - | Filter by symbol (e.g., "AAPL") |
| `msg_type` | string | - | Filter by message type (e.g., "D", "8") |
| `start_time` | datetime | - | Start time filter (ISO 8601 format) |
| `end_time` | datetime | - | End time filter (ISO 8601 format) |

**Example Request:**
```http
GET /api/messages?limit=100&symbol=AAPL&start_time=2025-01-07T10:00:00Z
```

**Response:**
```json
{
  "messages": [
    {
      "id": 12345,
      "msg_seq_num": 42,
      "sending_time": "2025-01-07T10:30:00.123456Z",
      "symbol": "AAPL",
      "msg_type": "D",
      "message": {
        "raw": {
          "8": "FIX.4.2",
          "35": "D",
          "55": "AAPL",
          "54": "1",
          "38": "100",
          "ingestion_timestamp": "2025-01-07T10:30:00.123456Z"
        },
        "enriched": {
          "tags": {
            "BeginString": {
              "tag": "8",
              "value": "FIX.4.2",
              "hr_value": "FIX.4.2"
            },
            "MsgType": {
              "tag": "35", 
              "value": "D",
              "hr_value": "D (NewOrderSingle)"
            }
          }
        }
      }
    }
  ],
  "pagination": {
    "limit": 100,
    "offset": 0,
    "total": 156789,
    "has_more": true
  }
}
```

#### Get Specific Message

Retrieve a specific message by its database ID.

```http
GET /api/message/{message_id}
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `message_id` | integer | Database ID of the message |

**Example Request:**
```http
GET /api/message/12345
```

**Response:**
```json
{
  "id": 12345,
  "msg_seq_num": 42,
  "sending_time": "2025-01-07T10:30:00.123456Z",
  "symbol": "AAPL",
  "msg_type": "D",
  "sender_comp_id": "CLIENT",
  "target_comp_id": "SERVER",
  "message": {
    "raw": { /* full raw message data */ },
    "enriched": { /* enriched message data */ }
  },
  "metadata": {
    "ingestion_timestamp": "2025-01-07T10:30:00.123456Z",
    "source": "socket",
    "processing_latency_ms": 0.85
  }
}
```

### Statistics API

#### Get Message Statistics

Retrieve aggregated statistics about message processing.

```http
GET /api/stats
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | "1h" | Time period ("5m", "1h", "1d", "1w") |
| `group_by` | string | - | Group by field ("symbol", "msg_type", "hour") |

**Example Request:**
```http
GET /api/stats?period=1h&group_by=symbol
```

**Response:**
```json
{
  "period": "1h",
  "start_time": "2025-01-07T09:30:00Z",
  "end_time": "2025-01-07T10:30:00Z",
  "total_messages": 45678,
  "parse_errors": 12,
  "avg_processing_latency_ms": 1.23,
  "groups": [
    {
      "key": "AAPL",
      "count": 15234,
      "percentage": 33.4
    },
    {
      "key": "GOOG", 
      "count": 12456,
      "percentage": 27.3
    }
  ]
}
```

#### Get System Health

Retrieve current system health and status information.

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-07T10:30:00Z",
  "uptime_seconds": 3600,
  "services": {
    "socket_listener": {
      "status": "running",
      "active_connections": 5,
      "total_messages": 156789
    },
    "kafka_producer": {
      "status": "connected",
      "broker_count": 3,
      "topic_partitions": 12
    },
    "database": {
      "status": "connected",
      "connection_pool_size": 10,
      "active_connections": 3
    },
    "prometheus": {
      "status": "running",
      "metrics_exported": 25
    }
  },
  "performance": {
    "current_throughput_msgs_sec": 1234,
    "avg_latency_ms": 0.95,
    "error_rate_percent": 0.02
  }
}
```

### Configuration API

#### Get Current Configuration

Retrieve the current system configuration (sensitive values masked).

```http
GET /api/config
```

**Response:**
```json
{
  "source": {
    "type": "socket",
    "host": "0.0.0.0",
    "port": 9876
  },
  "parser": {
    "protocol": "fix"
  },
  "filter": {
    "enabled": true,
    "include_only": {
      "55": ["AAPL", "GOOG", "MSFT"]
    }
  },
  "monitoring": {
    "enabled": true,
    "prometheus_port": 8000
  }
}
```

## Metrics Endpoints

### Prometheus Metrics

FixFeeder exposes Prometheus-compatible metrics for monitoring and alerting.

```http
GET /metrics
```

**Available Metrics:**

| Metric Name | Type | Description |
|-------------|------|-------------|
| `fix_messages_ingested_total` | Counter | Total FIX messages successfully parsed |
| `fix_parse_errors_total` | Counter | Total FIX messages that failed to parse |
| `fix_processing_latency_seconds` | Histogram | Message processing latency distribution |
| `fixfeeder_active_connections` | Gauge | Current active socket connections |
| `fixfeeder_uptime_seconds` | Counter | System uptime in seconds |
| `kafka_messages_sent_total` | Counter | Total messages sent to Kafka |
| `kafka_send_errors_total` | Counter | Total Kafka send failures |
| `database_writes_total` | Counter | Total database write operations |
| `database_write_errors_total` | Counter | Total database write failures |

**Example Metrics Output:**
```
# HELP fix_messages_ingested_total Total number of FIX messages successfully parsed
# TYPE fix_messages_ingested_total counter
fix_messages_ingested_total 156789

# HELP fix_parse_errors_total Total number of FIX messages that failed to parse  
# TYPE fix_parse_errors_total counter
fix_parse_errors_total 23

# HELP fix_processing_latency_seconds Message processing latency
# TYPE fix_processing_latency_seconds histogram
fix_processing_latency_seconds_bucket{le="0.001"} 145623
fix_processing_latency_seconds_bucket{le="0.005"} 156234
fix_processing_latency_seconds_bucket{le="0.01"} 156756
fix_processing_latency_seconds_bucket{le="+Inf"} 156789
fix_processing_latency_seconds_sum 187.543
fix_processing_latency_seconds_count 156789
```

### Custom Metrics

Add custom metrics for specific business requirements:

```python
from prometheus_client import Counter, Histogram, Gauge

# Custom business metrics
ORDERS_BY_SYMBOL = Counter('fix_orders_total', 'Orders by symbol', ['symbol'])
ORDER_SIZE_DISTRIBUTION = Histogram('fix_order_size', 'Order size distribution')
ACTIVE_SYMBOLS = Gauge('fix_active_symbols', 'Currently active symbols')
```

## WebSocket API

### Real-time Message Streaming

*Note: WebSocket API is planned for future release*

```javascript
// Connect to WebSocket endpoint
const ws = new WebSocket('ws://localhost:5001/ws/messages');

// Subscribe to specific symbols
ws.send(JSON.stringify({
  action: 'subscribe',
  symbols: ['AAPL', 'GOOG']
}));

// Receive real-time messages
ws.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log('New message:', message);
};
```

## Error Handling

### HTTP Status Codes

| Status Code | Description | Example Response |
|-------------|-------------|------------------|
| 200 | Success | Normal response with data |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Message or resource not found |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | Internal system error |
| 503 | Service Unavailable | System maintenance or overload |

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid limit parameter: must be between 1 and 1000",
    "details": {
      "parameter": "limit",
      "value": "5000",
      "allowed_range": "1-1000"
    }
  },
  "timestamp": "2025-01-07T10:30:00Z",
  "request_id": "req_123456789"
}
```

### Common Error Codes

| Error Code | Description | Resolution |
|------------|-------------|------------|
| `INVALID_PARAMETER` | Parameter validation failed | Check parameter format and ranges |
| `MESSAGE_NOT_FOUND` | Requested message doesn't exist | Verify message ID |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Implement request throttling |
| `INTERNAL_ERROR` | System error occurred | Check system logs |
| `SERVICE_UNAVAILABLE` | System overloaded | Retry with backoff |

## Rate Limiting

### Current Limits

| Endpoint | Rate Limit | Window |
|----------|------------|--------|
| `/api/messages` | 100 requests | 1 minute |
| `/api/message/{id}` | 1000 requests | 1 minute |
| `/api/stats` | 60 requests | 1 minute |
| `/metrics` | Unlimited | - |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1641559200
```

## Examples

### Python Client Example

```python
import requests
import json
from datetime import datetime, timedelta

class FixFeederClient:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url.rstrip('/')
    
    def get_recent_messages(self, limit=50, symbol=None):
        """Get recent messages with optional symbol filter."""
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        
        response = requests.get(f"{self.base_url}/api/messages", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_message(self, message_id):
        """Get specific message by ID."""
        response = requests.get(f"{self.base_url}/api/message/{message_id}")
        response.raise_for_status()
        return response.json()
    
    def get_stats(self, period="1h", group_by=None):
        """Get aggregated statistics."""
        params = {'period': period}
        if group_by:
            params['group_by'] = group_by
        
        response = requests.get(f"{self.base_url}/api/stats", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_health(self):
        """Get system health status."""
        response = requests.get(f"{self.base_url}/api/health")
        response.raise_for_status()
        return response.json()

# Usage example
client = FixFeederClient()

# Get recent AAPL messages
aapl_messages = client.get_recent_messages(limit=100, symbol="AAPL")
print(f"Found {len(aapl_messages['messages'])} AAPL messages")

# Get statistics for last hour grouped by symbol
stats = client.get_stats(period="1h", group_by="symbol")
print(f"Total messages: {stats['total_messages']}")

# Check system health
health = client.get_health()
print(f"System status: {health['status']}")
```

### curl Examples

```bash
# Get recent messages
curl -X GET "http://localhost:5001/api/messages?limit=10&symbol=AAPL" \
  -H "Accept: application/json"

# Get specific message
curl -X GET "http://localhost:5001/api/message/12345" \
  -H "Accept: application/json"

# Get statistics
curl -X GET "http://localhost:5001/api/stats?period=1h&group_by=symbol" \
  -H "Accept: application/json"

# Get system health
curl -X GET "http://localhost:5001/api/health" \
  -H "Accept: application/json"

# Get Prometheus metrics
curl -X GET "http://localhost:8000/metrics"
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

class FixFeederClient {
  constructor(baseUrl = 'http://localhost:5001') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }

  async getRecentMessages(options = {}) {
    const { limit = 50, symbol, startTime, endTime } = options;
    const params = { limit };
    
    if (symbol) params.symbol = symbol;
    if (startTime) params.start_time = startTime.toISOString();
    if (endTime) params.end_time = endTime.toISOString();

    const response = await this.client.get('/api/messages', { params });
    return response.data;
  }

  async getMessage(messageId) {
    const response = await this.client.get(`/api/message/${messageId}`);
    return response.data;
  }

  async getStats(period = '1h', groupBy = null) {
    const params = { period };
    if (groupBy) params.group_by = groupBy;

    const response = await this.client.get('/api/stats', { params });
    return response.data;
  }

  async getHealth() {
    const response = await this.client.get('/api/health');
    return response.data;
  }
}

// Usage example
async function example() {
  const client = new FixFeederClient();
  
  try {
    // Get recent messages
    const messages = await client.getRecentMessages({ 
      limit: 100, 
      symbol: 'AAPL' 
    });
    console.log(`Found ${messages.messages.length} messages`);

    // Get system health
    const health = await client.getHealth();
    console.log(`System status: ${health.status}`);
    
  } catch (error) {
    console.error('API Error:', error.response?.data || error.message);
  }
}

example();
```

This comprehensive API documentation provides all the necessary information for integrating with FixFeeder's REST API and monitoring endpoints.
