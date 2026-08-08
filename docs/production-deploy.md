# Production Deploy

Guide for deploying Thalor in production environments.

## Overview

This guide covers:
- Docker deployment (single host)
- Docker Compose deployment (multi-service)
- Kubernetes deployment (cluster)
- Security hardening
- Monitoring and logging
- Backup and recovery

## Single Host Deployment

### Prerequisites

- Linux server (Ubuntu 22.04+ recommended)
- Docker 24.0+
- Docker Compose v2.20+
- 16GB+ RAM
- 100GB+ SSD storage

### Installation

**1. Install Docker:**
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

**2. Install Docker Compose:**
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**3. Clone Thalor:**
```bash
git clone https://github.com/carlonox/Thalor.git
cd Thalor
```

**4. Configure:**
```bash
cp .env.example .env
nano .env  # Edit with production values
```

**5. Start:**
```bash
docker compose up -d
```

### Production .env

```bash
# Strong credentials
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD_HASH=$scrypt$...  # Generate with: hermes auth
DASHBOARD_PASSWORD=your-plaintext-password
DASHBOARD_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# LLM provider
LLM_API_KEY=your-production-api-key

# Router (if using)
ROUTER_ENCRYPTION_KEY=$(openssl rand -hex 32)
```

## Docker Compose Deployment

### Production Compose File

**docker-compose.prod.yml:**
```yaml
services:
  hermes:
    image: nousresearch/hermes-agent:latest
    container_name: thalor-agent
    restart: always
    ports:
      - "9999:9999"
      - "9119:9119"
    volumes:
      - hermes_data:/opt/data
      - hermes_vault:/mnt/vault
    environment:
      - HERMES_DASHBOARD=1
      - HERMES_HOME=/opt/data
      - DASHBOARD_USERNAME=${DASHBOARD_USERNAME}
      - DASHBOARD_PASSWORD_HASH=${DASHBOARD_PASSWORD_HASH}
      - DASHBOARD_SECRET=${DASHBOARD_SECRET}
    healthcheck:
      test: ["CMD", "bash", "-c", "curl -sf http://localhost:9119/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  freellmapi:
    image: ghcr.io/tashfeenahmed/freellmapi:latest
    container_name: thalor-router
    restart: always
    ports:
      - "3000:3000"
    volumes:
      - router_data:/app/server/data
    environment:
      - ENCRYPTION_KEY=${ROUTER_ENCRYPTION_KEY}
    healthcheck:
      test: ["CMD", "node", "-e", "require('http').get('http://localhost:3000/', r => process.exit(r.statusCode < 400 ? 0 : 1))"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  hermes_data:
  hermes_vault:
  router_data:

networks:
  default:
    driver: bridge
```

**Start production:**
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (v1.25+)
- kubectl configured
- Helm 3 (optional)

### Namespace

```bash
kubectl create namespace thalor
```

### ConfigMap

**configmap.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: thalor-config
  namespace: thalor
data:
  config.yaml: |
    model:
      default: deepseek-v4-flash
      provider: opencode-go
    agent:
      name: thalor-agent
      reasoning_effort: xhigh
    memory:
      provider: mnemosyne
      memory_enabled: false
    # ... rest of config
```

### Secret

**secret.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: thalor-secrets
  namespace: thalor
type: Opaque
stringData:
  llm-api-key: ***
  dashboard-password-hash: $scrypt$...
  dashboard-secret: your-secret
  router-encryption-key: your-64-char-hex
```

### Deployment

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thalor-agent
  namespace: thalor
spec:
  replicas: 1
  selector:
    matchLabels:
      app: thalor-agent
  template:
    metadata:
      labels:
        app: thalor-agent
    spec:
      containers:
      - name: hermes
        image: nousresearch/hermes-agent:latest
        ports:
        - containerPort: 9999
        - containerPort: 9119
        env:
        - name: HERMES_DASHBOARD
          value: "1"
        - name: HERMES_HOME
          value: "/opt/data"
        - name: DASHBOARD_USERNAME
          valueFrom:
            secretKeyRef:
              name: thalor-secrets
              key: dashboard-username
        - name: DASHBOARD_PASSWORD_HASH
          valueFrom:
            secretKeyRef:
              name: thalor-secrets
              key: dashboard-password-hash
        volumeMounts:
        - name: data
          mountPath: /opt/data
        - name: config
          mountPath: /opt/data/config.yaml
          subPath: config.yaml
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /
            port: 9999
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: 9999
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: thalor-data
      - name: config
        configMap:
          name: thalor-config
```

### PersistentVolumeClaim

**pvc.yaml:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: thalor-data
  namespace: thalor
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: standard
```

### Service

**service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: thalor-agent
  namespace: thalor
spec:
  selector:
    app: thalor-agent
  ports:
  - name: dashboard
    port: 9999
    targetPort: 9999
  - name: gateway
    port: 9119
    targetPort: 9119
  type: ClusterIP
```

### Ingress

**ingress.yaml:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: thalor-ingress
  namespace: thalor
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - thalor.example.com
    secretName: thalor-tls
  rules:
  - host: thalor.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: thalor-agent
            port:
              number: 9999
```

**Apply all:**
```bash
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

## Security Hardening

### 1. Strong Authentication

**Generate strong passwords:**
```bash
# Dashboard password (scrypt hash)
hermes auth

# Secrets
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Encryption keys
openssl rand -hex 32
```

### 2. HTTPS/TLS

**Option A: Reverse Proxy (nginx)**

**nginx.conf:**
```nginx
server {
    listen 443 ssl http2;
    server_name thalor.example.com;

    ssl_certificate /etc/letsencrypt/live/thalor.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/thalor.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:9999;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name thalor.example.com;
    return 301 https://$server_name$request_uri;
}
```

**Option B: Kubernetes Ingress with cert-manager**

Install cert-manager:
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

Create ClusterIssuer:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

### 3. Network Isolation

**Docker network:**
```yaml
networks:
  thalor-internal:
    driver: bridge
    internal: true  # No external access
  thalor-external:
    driver: bridge

services:
  hermes:
    networks:
      - thalor-internal
      - thalor-external
  
  database:
    networks:
      - thalor-internal  # Only internal access
```

### 4. Secrets Management

**Option A: Docker Secrets**
```bash
echo "your-api-key" | docker secret create llm_api_key -
```

**docker-compose.yml:**
```yaml
services:
  hermes:
    secrets:
      - llm_api_key

secrets:
  llm_api_key:
    external: true
```

**Option B: Kubernetes Secrets**
```bash
kubectl create secret generic thalor-secrets \
  --from-literal=llm-api-key=your-key \
  --namespace=thalor
```

### 5. Rate Limiting

**nginx rate limiting:**
```nginx
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    server {
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://localhost:9119;
        }
    }
}
```

## Monitoring and Logging

### 1. Docker Logs

```bash
# View logs
docker logs thalor-agent

# Follow logs
docker logs -f thalor-agent

# Last 100 lines
docker logs --tail 100 thalor-agent
```

### 2. Prometheus + Grafana

**docker-compose.monitoring.yml:**
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
```

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'thalor'
    static_configs:
      - targets: ['thalor-agent:9119']
```

### 3. Health Checks

**Custom health endpoint:**
```python
# health-check.py
from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/health")
def health():
    checks = {
        "hermes": check_hermes(),
        "mnemosyne": check_mnemosyne(),
        "ollama": check_ollama()
    }
    
    status = "healthy" if all(checks.values()) else "unhealthy"
    
    return {
        "status": status,
        "checks": checks
    }

def check_hermes():
    try:
        r = requests.get("http://localhost:9999/", timeout=5)
        return r.status_code == 200
    except:
        return False

def check_mnemosyne():
    # Check database
    pass

def check_ollama():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        return r.status_code == 200
    except:
        return False
```

## Backup and Recovery

### 1. Automated Backups

**backup.sh:**
```bash
#!/bin/bash

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="thalor-backup-$DATE.tar.gz"

# Backup data volume
docker run --rm \
  -v thalor_hermes_data:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/$BACKUP_FILE -C /data .

# Keep only last 7 days
find $BACKUP_DIR -name "thalor-backup-*.tar.gz" -mtime +7 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/$BACKUP_FILE s3://your-backup-bucket/
```

**Cron job:**
```bash
# Daily at 2 AM
0 2 * * * /path/to/backup.sh
```

### 2. Recovery

**Restore from backup:**
```bash
# Stop services
docker compose down

# Restore data
docker run --rm \
  -v thalor_hermes_data:/data \
  -v /backups:/backup \
  alpine tar xzf /backup/thalor-backup-20260808_020000.tar.gz -C /data

# Start services
docker compose up -d
```

### 3. Disaster Recovery

**Off-site backups:**
- S3/GCS/Azure Blob
- Separate geographic region
- Encrypted at rest

**Recovery procedure:**
1. Provision new server
2. Install Docker
3. Clone Thalor repo
4. Restore from backup
5. Update DNS (if needed)
6. Verify functionality

## Scaling

### Horizontal Scaling

**Multiple agent instances:**
```yaml
services:
  hermes-1:
    image: nousresearch/hermes-agent:latest
    # ... config
  
  hermes-2:
    image: nousresearch/hermes-agent:latest
    # ... config
  
  load-balancer:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

**nginx.conf:**
```nginx
upstream thalor_agents {
    server hermes-1:9999;
    server hermes-2:9999;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://thalor_agents;
    }
}
```

### Vertical Scaling

**Increase resources:**
```yaml
services:
  hermes:
    deploy:
      resources:
        limits:
          memory: 8G  # Up from 4G
          cpus: '4.0'  # Up from 2.0
```

## Maintenance

### Updates

**Update Hermes image:**
```bash
docker compose pull
docker compose up -d
```

**Rollback if needed:**
```bash
docker compose down
docker compose -f docker-compose.rollback.yml up -d
```

### Log Rotation

**Docker log rotation:**
```yaml
services:
  hermes:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Database Maintenance

**Vacuum SQLite:**
```bash
docker exec thalor-agent bash -c "sqlite3 /opt/data/mnemosyne/data/mnemosyne.db 'VACUUM'"
```

**Archive old memories:**
```bash
docker exec thalor-agent bash -c "mnemosyne archive --older-than 365"
```

## Checklist

Before going to production:

- [ ] Strong passwords and secrets generated
- [ ] HTTPS/TLS configured
- [ ] Health checks passing
- [ ] Backups automated and tested
- [ ] Monitoring configured
- [ ] Log rotation enabled
- [ ] Resource limits set
- [ ] Network isolation configured
- [ ] Rate limiting enabled
- [ ] Disaster recovery tested
- [ ] Documentation updated
- [ ] Team trained

## Further Reading

- [Docker Production Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Production Guidelines](https://kubernetes.io/docs/setup/best-practices/)
- [Security Hardening Guide](https://cisecurity.org/benchmark/docker)
