# Installation Guide: GitLab to RHEL 9

Complete guide to install ZainOne Orchestrator Studio from GitLab on Red Hat Enterprise Linux 9.

---

## Prerequisites

1. **Red Hat Enterprise Linux 9** server with:
   - Root or sudo access
   - Internet connectivity
   - At least 4GB RAM, 2 CPU cores, 20GB disk space

2. **GitLab Access**:
   - GitLab account with access to `https://gitlab.com/muhammedali275/ai-orchestrator.git`
   - SSH key or HTTPS credentials configured

---

## Step 1: System Preparation

### Update System
```bash
sudo dnf update -y
```

### Install Essential Tools
```bash
sudo dnf install -y git curl wget vim
```

---

## Step 2: Install Python 3.11+

```bash
# Install Python 3.11
sudo dnf install -y python3.11 python3.11-pip python3.11-devel

# Verify installation
python3.11 --version

# Create symlink (optional, for convenience)
sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3.11 1

# Upgrade pip
python3.11 -m pip install --upgrade pip
```

---

## Step 3: Install Node.js 20+

```bash
# Add NodeSource repository for Node.js 20
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -

# Install Node.js
sudo dnf install -y nodejs

# Verify installation
node --version  # Should be v20.x
npm --version   # Should be 10.x
```

---

## Step 4: Clone Repository from GitLab

### Option A: HTTPS (with credentials)
```bash
# Navigate to installation directory
cd /opt

# Clone repository
sudo git clone https://gitlab.com/muhammedali275/ai-orchestrator.git zainone-orchestrator

# Change ownership
sudo chown -R $USER:$USER zainone-orchestrator
cd zainone-orchestrator
```

### Option B: SSH (recommended for automation)
```bash
# First, set up SSH key for GitLab if not already done:
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub
# Add this public key to GitLab: Settings → SSH Keys

# Clone repository
cd /opt
sudo git clone git@gitlab.com:muhammedali275/ai-orchestrator.git zainone-orchestrator
sudo chown -R $USER:$USER zainone-orchestrator
cd zainone-orchestrator
```

---

## Step 5: Install Backend Dependencies

```bash
# Navigate to repository root
cd /opt/zainone-orchestrator

# Install Python dependencies
python3.11 -m pip install --user -r requirements.txt

# Or use a virtual environment (recommended):
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Key dependencies installed:**
- FastAPI, Uvicorn (API server)
- LangChain, LangGraph (AI orchestration)
- SQLAlchemy, Alembic (database)
- Redis, psycopg2 (optional backends)
- httpx, cryptography, psutil

---

## Step 6: Install Frontend Dependencies

```bash
# Navigate to frontend directory
cd /opt/zainone-orchestrator/frontend

# Install npm packages
npm install

# Build production frontend
npm run build
```

This creates an optimized production build in `frontend/build/`.

---

## Step 7: Configure Environment

### Create Backend Configuration
```bash
# Copy example environment file
cd /opt/zainone-orchestrator/backend/orchestrator
cp .env.example .env

# Edit configuration
vim .env
```

**Minimal `.env` configuration:**
```bash
# Application
APP_NAME="ZainOne Orchestrator Studio"
APP_VERSION="1.0.0"
DEBUG=false

# LLM Configuration (Ollama example)
LLM_BASE_URL=http://localhost:11434
LLM_DEFAULT_MODEL=llama2
LLM_API_KEY=""
LLM_TIMEOUT_SECONDS=120

# Database (optional - uses in-memory by default)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=orchestrator
POSTGRES_USER=orchestrator
POSTGRES_PASSWORD=your_secure_password

# Redis Cache (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=""

# Security
SECRET_KEY=$(openssl rand -hex 32)
CREDENTIALS_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Server
HOST=0.0.0.0
PORT=8000
```

### Set Permissions
```bash
chmod 600 /opt/zainone-orchestrator/backend/orchestrator/.env
```

---

## Step 8: Install Optional Services

### Install Ollama (for local LLM)
```bash
# Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull a model
ollama pull llama2
```

### Install PostgreSQL (optional)
```bash
sudo dnf install -y postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create database
sudo -u postgres psql -c "CREATE USER orchestrator WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "CREATE DATABASE orchestrator OWNER orchestrator;"
```

### Install Redis (optional)
```bash
sudo dnf install -y redis
sudo systemctl enable redis
sudo systemctl start redis
```

---

## Step 9: Configure Firewall

```bash
# Allow backend API port
sudo firewall-cmd --permanent --add-port=8000/tcp

# Allow frontend port (if serving separately)
sudo firewall-cmd --permanent --add-port=3000/tcp

# Reload firewall
sudo firewall-cmd --reload
```

---

## Step 10: Create Systemd Services

### Backend Service
```bash
sudo vim /etc/systemd/system/zainone-backend.service
```

```ini
[Unit]
Description=ZainOne Orchestrator Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/zainone-orchestrator/backend/orchestrator
Environment="PATH=/opt/zainone-orchestrator/venv/bin:/usr/local/bin:/usr/bin"
ExecStart=/opt/zainone-orchestrator/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Frontend Service (using serve)
```bash
# Install serve globally
sudo npm install -g serve

sudo vim /etc/systemd/system/zainone-frontend.service
```

```ini
[Unit]
Description=ZainOne Orchestrator Frontend
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/zainone-orchestrator/frontend
ExecStart=/usr/bin/serve -s build -l 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable zainone-backend
sudo systemctl enable zainone-frontend

# Start services
sudo systemctl start zainone-backend
sudo systemctl start zainone-frontend

# Check status
sudo systemctl status zainone-backend
sudo systemctl status zainone-frontend
```

---

## Step 11: Configure Nginx (Production Setup)

```bash
# Install Nginx
sudo dnf install -y nginx

# Create configuration
sudo vim /etc/nginx/conf.d/zainone.conf
```

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;  # Change to your domain or IP

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check
    location /health {
        proxy_pass http://backend;
    }

    # API docs
    location /docs {
        proxy_pass http://backend;
    }
}
```

```bash
# Test Nginx configuration
sudo nginx -t

# Enable and start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Allow HTTP/HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## Step 12: SSL/TLS with Let's Encrypt (Optional)

```bash
# Install certbot
sudo dnf install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
sudo systemctl enable certbot-renew.timer
```

---

## Step 13: Verify Installation

### Check Services
```bash
# Check backend
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# View logs
sudo journalctl -u zainone-backend -f
sudo journalctl -u zainone-frontend -f
```

### Access Application
- **Frontend**: `http://your-server-ip:3000` or `http://your-domain.com`
- **Backend API**: `http://your-server-ip:8000/docs`
- **Health Check**: `http://your-server-ip:8000/health`

---

## Step 14: Update from GitLab

To pull latest changes:

```bash
cd /opt/zainone-orchestrator

# Pull latest code
git pull origin main

# Update backend dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Update frontend
cd frontend
npm install
npm run build

# Restart services
sudo systemctl restart zainone-backend
sudo systemctl restart zainone-frontend
```

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
sudo journalctl -u zainone-backend -n 50

# Test manually
cd /opt/zainone-orchestrator/backend/orchestrator
source ../../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend build fails
```bash
# Clear cache and rebuild
cd /opt/zainone-orchestrator/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Port already in use
```bash
# Find process using port 8000
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Permission issues
```bash
# Fix ownership
sudo chown -R $USER:$USER /opt/zainone-orchestrator

# Fix .env permissions
chmod 600 /opt/zainone-orchestrator/backend/orchestrator/.env
```

---

## Security Checklist

- [ ] Changed default passwords in `.env`
- [ ] Generated secure `SECRET_KEY` and `CREDENTIALS_ENCRYPTION_KEY`
- [ ] Configured firewall rules
- [ ] Set up SSL/TLS certificates
- [ ] Restricted `.env` file permissions (600)
- [ ] Running services as non-root user
- [ ] Regular backup of database and credentials
- [ ] Monitoring logs for security issues

---

## Quick Start Commands

```bash
# One-line installation (after prerequisites)
cd /opt && \
  sudo git clone https://gitlab.com/muhammedali275/ai-orchestrator.git zainone-orchestrator && \
  sudo chown -R $USER:$USER zainone-orchestrator && \
  cd zainone-orchestrator && \
  python3.11 -m venv venv && \
  source venv/bin/activate && \
  pip install -r requirements.txt && \
  cd frontend && \
  npm install && \
  npm run build

# Start manually (for testing)
cd /opt/zainone-orchestrator/backend/orchestrator
source ../../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# In another terminal:
cd /opt/zainone-orchestrator/frontend
npx serve -s build -l 3000 &
```

---

## Support

For issues:
1. Check logs: `sudo journalctl -u zainone-backend -f`
2. Verify services: `sudo systemctl status zainone-backend zainone-frontend`
3. Test connectivity: `curl http://localhost:8000/health`
4. Review GitLab repository: https://gitlab.com/muhammedali275/ai-orchestrator

---

**Installation complete!** 🎉

Access your orchestrator at `http://your-server-ip` or configured domain.
