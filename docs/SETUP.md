# FixFeeder Setup Guide

This guide provides detailed instructions for setting up and configuring FixFeeder in different environments.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Environment](#development-environment)
- [Production Deployment](#production-deployment)
- [Configuration Guide](#configuration-guide)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

Ensure you have the following installed:
- **Docker**: Version 20.10+ recommended
- **Docker Compose**: Version 1.29+ recommended
- **Git**: For cloning the repository

### 1. Clone and Start

```bash
# Clone the repository
git clone https://github.com/your-username/FixFeeder.git
cd FixFeeder

# Start all services
docker-compose up --build
```

### 2. Verify Installation

Check that all services are running:

```bash
# Check service status
docker-compose ps

# Expected output:
# NAME                COMMAND             SERVICE             STATUS              PORTS
# fixfeeder-fixfeeder-1   "python main.py"    fixfeeder           running             0.0.0.0:5001->5001/tcp, 0.0.0.0:8000->8000/tcp, 0.0.0.0:9876->9876/tcp
# fixfeeder-grafana-1     "/run.sh"           grafana             running             0.0.0.0:3000->3000/tcp
# fixfeeder-kafka-1       "/opt/bitnami/scr..."   kafka               running             0.0.0.0:9092->9092/tcp
# fixfeeder-postgres-1    "docker-entrypoint..."  postgres            running             0.0.0.0:5432->5432/tcp
# fixfeeder-prometheus-1  "/bin/prometheus ..."   prometheus          running             0.0.0.0:9090->9090/tcp
# fixfeeder-zookeeper-1   "/opt/bitnami/scr..."   zookeeper           running             2181/tcp
```

### 3. Access Services

- **FixFeeder Dashboard**: http://localhost:5001
- **Grafana Monitoring**: http://localhost:3000 (admin/admin)
- **Prometheus Metrics**: http://localhost:9090
- **Socket for FIX Messages**: `localhost:9876`

## Development Environment

### Local Python Development

For active development without rebuilding Docker containers:

1. **Start Infrastructure Services Only:**
   ```bash
   docker-compose up kafka postgres prometheus grafana zookeeper
   ```

2. **Install Python Dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run FixFeeder Locally:**
   ```bash
   python main.py
   ```

### Hot Reload Development

For rapid development with code changes:

1. **Modify docker-compose.yml** to mount local code:
   ```yaml
   fixfeeder:
     build: .
     volumes:
       - ./:/app
       - ./config:/app/config
     environment:
       - FLASK_ENV=development
   ```

2. **Use development configuration:**
   ```bash
   cp config/config.yml config/config.dev.yml
   # Edit config.dev.yml for development settings
   FIXFEEDER_CONFIG=config/config.dev.yml docker-compose up
   ```

## Production Deployment

### Security Considerations

1. **Change Default Passwords:**
   ```yaml
   # config/config.yml
   storage:
     postgres_config:
       password: "your-secure-password-here"
   ```

2. **Use Environment Variables:**
   ```bash
   export POSTGRES_PASSWORD=your-secure-password
   export KAFKA_SECURITY_PROTOCOL=SASL_SSL
   ```

3. **Network Security:**
   ```yaml
   # docker-compose.prod.yml
   services:
     fixfeeder:
       ports:
         - "127.0.0.1:9876:9876"  # Bind to localhost only
   ```

### Performance Tuning

1. **Kafka Configuration:**
   ```yaml
   kafka:
     environment:
       - KAFKA_CFG_NUM_NETWORK_THREADS=8
       - KAFKA_CFG_NUM_IO_THREADS=16
       - KAFKA_CFG_SOCKET_SEND_BUFFER_BYTES=102400
       - KAFKA_CFG_SOCKET_RECEIVE_BUFFER_BYTES=102400
   ```

2. **PostgreSQL Tuning:**
   ```yaml
   postgres:
     environment:
       - POSTGRES_SHARED_BUFFERS=256MB
       - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
   ```

3. **FixFeeder Configuration:**
   ```yaml
   core:
     log_level: WARNING  # Reduce logging overhead
   
   queue:
     batch_size: 1000   # Batch messages for efficiency
   ```

### High Availability Setup

1. **Multiple FixFeeder Instances:**
   ```yaml
   fixfeeder-1:
     build: .
     ports:
       - "9876:9876"
   
   fixfeeder-2:
     build: .
     ports:
       - "9877:9876"
   ```

2. **Load Balancer Configuration:**
   ```nginx
   upstream fixfeeder {
       server localhost:9876;
       server localhost:9877;
   }
   ```

## Configuration Guide

### Source Configuration

#### Socket Listener
```yaml
source:
  type: socket
  host: 0.0.0.0      # Bind address
  port: 9876         # TCP port
```

#### File Reader
```yaml
source:
  type: file
  file_path: /data/fix_messages.log
```

#### Kafka Consumer
```yaml
source:
  type: kafka
  kafka_brokers: ["kafka1:9092", "kafka2:9092"]
  kafka_topic: "raw-fix-messages"
```

#### Replay Engine
```yaml
source:
  type: replay
  file_path: /data/historical_messages.log
  speed_multiplier: 2.0  # 2x speed replay
```

### Filter Configuration

Filter messages by symbol, message type, or custom criteria:

```yaml
filter:
  enabled: true
  include_only:
    "55": ["AAPL", "GOOG", "MSFT"]    # Symbols
    "35": ["D", "8", "9"]             # Message types
  exclude:
    "49": ["TEST_SENDER"]             # Exclude test senders
```

### Storage Configuration

#### PostgreSQL (Recommended for Production)
```yaml
storage:
  type: postgresql
  postgres_config:
    user: fixfeeder
    password: secure_password
    host: postgres.company.com
    port: 5432
    database: fixfeeder_prod
    connection_pool_size: 20
```

#### SQLite (Development/Testing)
```yaml
storage:
  type: sqlite
  path: /data/fixfeeder.db
```

### Monitoring Configuration

```yaml
monitoring:
  enabled: true
  prometheus_port: 8000
  metrics_interval: 10  # seconds
  custom_labels:
    environment: production
    datacenter: us-east-1
```

## Troubleshooting

### Common Issues

#### 1. "Connection refused" on port 9876
**Problem**: FixFeeder socket listener not started
**Solution**:
```bash
# Check if FixFeeder is running
docker-compose ps fixfeeder

# Check logs
docker-compose logs fixfeeder

# Restart if needed
docker-compose restart fixfeeder
```

#### 2. Kafka connection failures
**Problem**: Kafka not ready when FixFeeder starts
**Solution**:
```yaml
# Add health checks to docker-compose.yml
kafka:
  healthcheck:
    test: ["CMD", "kafka-topics.sh", "--list", "--bootstrap-server", "localhost:9092"]
    interval: 30s
    timeout: 10s
    retries: 5

fixfeeder:
  depends_on:
    kafka:
      condition: service_healthy
```

#### 3. PostgreSQL connection errors
**Problem**: Database not ready or wrong credentials
**Solution**:
```bash
# Test database connection
docker-compose exec postgres psql -U user -d fixfeeder -c "SELECT 1;"

# Check database logs
docker-compose logs postgres
```

#### 4. High memory usage
**Problem**: Large message volumes causing memory buildup
**Solution**:
```yaml
# Reduce batch sizes
queue:
  batch_size: 100

# Increase processing frequency
storage:
  commit_interval: 1000
```

### Performance Debugging

#### Monitor Resource Usage
```bash
# Check container resource usage
docker stats

# Monitor specific container
docker stats fixfeeder_fixfeeder_1
```

#### Database Performance
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('fixfeeder'));

-- Check table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
FROM pg_tables 
WHERE schemaname = 'public';

-- Check active connections
SELECT count(*) FROM pg_stat_activity;
```

#### Kafka Performance
```bash
# Check topic lag
docker-compose exec kafka kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group fixfeeder_consumer

# Monitor topic statistics
docker-compose exec kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe --topic fix.messages
```

### Log Analysis

#### FixFeeder Logs
```bash
# Follow logs in real-time
docker-compose logs -f fixfeeder

# Search for errors
docker-compose logs fixfeeder | grep ERROR

# Filter by component
docker-compose logs fixfeeder | grep SocketListener
```

#### Log Levels
Adjust logging verbosity in `config.yml`:
```yaml
core:
  log_level: DEBUG   # DEBUG, INFO, WARNING, ERROR
```

### Health Checks

Create a simple health check script:

```bash
#!/bin/bash
# health_check.sh

# Check FixFeeder socket
nc -z localhost 9876 || echo "FixFeeder socket DOWN"

# Check dashboard
curl -f http://localhost:5001/health || echo "Dashboard DOWN"

# Check metrics
curl -f http://localhost:8000/metrics || echo "Metrics DOWN"

echo "Health check complete"
```

### Backup and Recovery

#### Database Backup
```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U user fixfeeder > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U user fixfeeder < backup.sql
```

#### Configuration Backup
```bash
# Backup configuration
tar -czf fixfeeder-config-$(date +%Y%m%d).tar.gz config/

# Version control recommended
git add config/ && git commit -m "Update configuration"
```

## Support

For additional support:
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check the main README and architecture docs
- **Community**: Join our Discord server for real-time support
- **Professional Support**: Contact us for enterprise support options
