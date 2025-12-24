# Complete Guide: Deploy to RHEL 9 Production via Git + Continuous VS Code Development

This guide covers uploading your app code to a RHEL 9 production server using Git and setting up continuous development from VS Code.

---

## Table of Contents
1. [Port Configuration Summary](#port-configuration-summary)
2. [Initial Deployment to RHEL 9](#initial-deployment-to-rhel-9)
3. [Continuous Development with VS Code](#continuous-development-with-vs-code)
4. [Update Workflow](#update-workflow)
5. [Troubleshooting](#troubleshooting)

---

## Port Configuration Summary

### Application Ports (Verified from Codebase)

| Component | Port | Environment Variable | Default Value |
|-----------|------|---------------------|---------------|
| **Backend API** | 8000 | `API_PORT` | `8000` |
| **Frontend Dev Server** | 3000 | N/A | `3000` |
| **LLM Server (Ollama)** | 11434 | `LLM_BASE_URL` | `http://localhost:11434` |
| **PostgreSQL** | 5432 | `POSTGRES_PORT` | `5432` |
| **Redis Cache** | 6379 | `REDIS_PORT` | `6379` |

### Backend API Endpoints (Port 8000)
- Health Check: `http://localhost:8000/health`
- API Docs: `http://localhost:8000/docs`
- LLM Config: `http://localhost:8000/api/llm/config`
- Chat UI: `http://localhost:8000/api/chat/ui/*`
- Agents: `http://localhost:8000/api/agents`
- Tools: `http://localhost:8000/api/tools`
- Credentials: `http://localhost:8000/api/credentials`
- Monitoring: `http://localhost:8000/api/monitoring/*`

### Frontend URLs (Port 3000 in dev, 80/443 in production)
- Main Dashboard: `/`
- Chat Studio: `/chat`
- LLM Connections: `/llm`
- Agents Config: `/agents`
- Tools & Data Sources: `/tools`
- Credentials: `/credentials`

---

## Initial Deployment to RHEL 9

### Method 1: Direct Git Clone from GitLab (Recommended)

#### Step 1: Prepare RHEL 9 Server

```bash
# SSH into your RHEL 9 server
ssh username@your-rhel9-server-ip

# Update system
sudo dnf update -y

# Install Git
sudo dnf install -y git

# Install Python 3.11+
sudo dnf install -y python3.11 python3.11-pip python3.11-devel

# Install Node.js 20
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs

# Verify installations
python3.11 --version  # Should show 3.11.x
node --version        # Should show v20.x
git --version         # Should show 2.x
```

#### Step 2: Clone Repository from GitLab

```bash
# Navigate to installation directory
cd /opt

# Clone from GitLab (HTTPS)
sudo git clone https://gitlab.com/muhammedali275/ai-orchestrator.git zainone-orchestrator

# Or use SSH (if you have SSH key configured)
# sudo git clone git@gitlab.com:muhammedali275/ai-orchestrator.git zainone-orchestrator

# Set ownership
sudo chown -R $USER:$USER zainone-orchestrator
cd zainone-orchestrator

# Verify
git status
git log -1  # Should show your latest commit
```

#### Step 3: Install Backend Dependencies

```bash
# Navigate to repo root
cd /opt/zainone-orchestrator

# Create Python virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
pip list | grep uvicorn
```

#### Step 4: Install Frontend Dependencies & Build

```bash
# Navigate to frontend
cd /opt/zainone-orchestrator/frontend

# Install dependencies
npm install

# Build production bundle
npm run build

# Verify build
ls -la build/
```

#### Step 5: Configure Environment

```bash
# Navigate to backend config
cd /opt/zainone-orchestrator/backend/orchestrator

# Create .env from example (if exists) or create new
cat > .env << 'EOF'
# Application
APP_NAME="ZainOne Orchestrator Studio"
APP_VERSION="1.0.0"
DEBUG=false

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://your-server-ip,http://your-domain.com

# LLM Configuration
LLM_BASE_URL=http://localhost:11434
LLM_DEFAULT_MODEL=llama2
LLM_API_KEY=
LLM_TIMEOUT_SECONDS=120

# Database (PostgreSQL - Optional)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=orchestrator
POSTGRES_USER=orchestrator
POSTGRES_PASSWORD=CHANGE_ME_SECURE_PASSWORD

# Redis Cache (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Security
SECRET_KEY=$(openssl rand -hex 32)
CREDENTIALS_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Monitoring
MONITORING_EXPORT_INTERVAL=60
EOF

# Secure the file
chmod 600 .env

# Edit with your actual values
vim .env  # or nano .env
```

#### Step 6: Configure Firewall

```bash
# Allow backend API port
sudo firewall-cmd --permanent --add-port=8000/tcp

# Allow HTTP/HTTPS for reverse proxy
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Reload firewall
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-all
```

#### Step 7: Create Systemd Services

**Backend Service:**

```bash
sudo tee /etc/systemd/system/zainone-backend.service << 'EOF'
[Unit]
Description=ZainOne Orchestrator Backend API
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/zainone-orchestrator/backend/orchestrator
Environment="PATH=/opt/zainone-orchestrator/venv/bin:/usr/local/bin:/usr/bin"
ExecStart=/opt/zainone-orchestrator/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Replace YOUR_USERNAME with your actual username
sudo sed -i "s/YOUR_USERNAME/$USER/g" /etc/systemd/system/zainone-backend.service
```

**Frontend Service (using serve):**

```bash
# Install serve globally
sudo npm install -g serve

sudo tee /etc/systemd/system/zainone-frontend.service << 'EOF'
[Unit]
Description=ZainOne Orchestrator Frontend
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/zainone-orchestrator/frontend
ExecStart=/usr/bin/serve -s build -l 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Replace YOUR_USERNAME
sudo sed -i "s/YOUR_USERNAME/$USER/g" /etc/systemd/system/zainone-frontend.service
```

**Enable and Start Services:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable zainone-backend
sudo systemctl enable zainone-frontend

# Start services
sudo systemctl start zainone-backend
sudo systemctl start zainone-frontend

# Check status
sudo systemctl status zainone-backend
sudo systemctl status zainone-frontend

# Check logs
sudo journalctl -u zainone-backend -f
sudo journalctl -u zainone-frontend -f
```

---

## Continuous Development with VS Code

### Option 1: SSH Remote Development (Recommended)

This allows you to edit files directly on the production server using VS Code.

#### Step 1: Install VS Code Remote - SSH Extension

1. Open VS Code on your Windows machine
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Remote - SSH"
4. Install the official Microsoft extension

#### Step 2: Configure SSH Connection

1. Press `F1` or `Ctrl+Shift+P`
2. Type "Remote-SSH: Open SSH Configuration File"
3. Select your SSH config file (usually `C:\Users\YourName\.ssh\config`)
4. Add your server configuration:

```ssh-config
Host rhel9-prod
    HostName your-server-ip-or-domain
    User your-username
    Port 22
    IdentityFile C:\Users\YourName\.ssh\id_rsa
```

#### Step 3: Connect to Server

1. Press `F1` → "Remote-SSH: Connect to Host..."
2. Select `rhel9-prod`
3. VS Code will connect and install the VS Code Server on RHEL 9
4. Once connected, click "Open Folder" → `/opt/zainone-orchestrator`

#### Step 4: Edit Files & Auto-Restart

When editing files directly on the server:

**Backend (auto-reload in development):**
```bash
# Stop production service
sudo systemctl stop zainone-backend

# Run in development mode (in VS Code terminal)
cd /opt/zainone-orchestrator/backend/orchestrator
source ../../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Changes to Python files will auto-reload!
```

**Frontend (rebuild required):**
```bash
# In VS Code terminal
cd /opt/zainone-orchestrator/frontend
npm run build

# Restart frontend service
sudo systemctl restart zainone-frontend
```

---

### Option 2: Git Push/Pull Workflow

Edit locally on Windows, push to GitLab, pull on production server.

#### On Your Windows Development Machine:

```powershell
# Make changes in VS Code
# Commit and push to GitLab
git add -A
git commit -m "your changes description"
git push origin main
```

#### On Your RHEL 9 Production Server:

```bash
# Pull latest changes
cd /opt/zainone-orchestrator
git pull origin main

# Update backend dependencies (if requirements.txt changed)
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Rebuild frontend (if frontend code changed)
cd frontend
npm install
npm run build

# Restart services
sudo systemctl restart zainone-backend
sudo systemctl restart zainone-frontend
```

**Create an update script for convenience:**

```bash
cat > /opt/zainone-orchestrator/update-from-git.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 Updating ZainOne Orchestrator from GitLab..."

cd /opt/zainone-orchestrator

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Update backend
echo "🐍 Updating Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Update frontend
echo "⚛️  Rebuilding frontend..."
cd frontend
npm install
npm run build
cd ..

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart zainone-backend
sudo systemctl restart zainone-frontend

echo "✅ Update complete!"
echo "Backend: http://$(hostname -I | awk '{print $1}'):8000"
echo "Frontend: http://$(hostname -I | awk '{print $1}'):3000"
EOF

chmod +x /opt/zainone-orchestrator/update-from-git.sh

# Usage:
# ./update-from-git.sh
```

---

## Update Workflow

### Quick Update Commands

**From your Windows machine:**
```powershell
# Commit and push changes
git add -A
git commit -m "feat: add new feature"
git push origin main
```

**On RHEL 9 server:**
```bash
# Quick update
cd /opt/zainone-orchestrator
./update-from-git.sh
```

**OR manually:**
```bash
cd /opt/zainone-orchestrator
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
cd frontend && npm install && npm run build
sudo systemctl restart zainone-backend zainone-frontend
```

---

## Troubleshooting

### Check Service Status

```bash
# Check if services are running
sudo systemctl status zainone-backend
sudo systemctl status zainone-frontend

# View live logs
sudo journalctl -u zainone-backend -f
sudo journalctl -u zainone-frontend -f

# Test backend API
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Test frontend
curl http://localhost:3000
```

### Port Already in Use

```bash
# Find process using port 8000
sudo lsof -i :8000
sudo kill -9 <PID>

# Or use fuser
sudo fuser -k 8000/tcp
```

### Git Pull Conflicts

```bash
# If you have local changes conflicting with remote
cd /opt/zainone-orchestrator

# Option 1: Stash local changes
git stash
git pull origin main
git stash pop

# Option 2: Reset to remote (CAUTION: loses local changes)
git fetch origin
git reset --hard origin/main
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R $USER:$USER /opt/zainone-orchestrator

# Fix .env permissions
chmod 600 /opt/zainone-orchestrator/backend/orchestrator/.env
```

### Backend Won't Start

```bash
# Check Python environment
cd /opt/zainone-orchestrator
source venv/bin/activate
python --version
pip list | grep -E "fastapi|uvicorn|pydantic"

# Test manually
cd backend/orchestrator
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Check error messages
```

### Frontend Build Fails

```bash
# Clear cache and rebuild
cd /opt/zainone-orchestrator/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## Nginx Reverse Proxy (Production Setup)

For production, serve both frontend and backend through Nginx on port 80/443:

```bash
sudo dnf install -y nginx

sudo tee /etc/nginx/conf.d/zainone.conf << 'EOF'
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain or IP

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
EOF

# Test Nginx config
sudo nginx -t

# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## Summary of Ports

| Service | Port | Access |
|---------|------|--------|
| **Backend API** | 8000 | Internal + API clients |
| **Frontend (Dev)** | 3000 | Internal + Dev access |
| **Nginx (Production)** | 80/443 | Public access |
| **Ollama LLM** | 11434 | Localhost only |
| **PostgreSQL** | 5432 | Localhost only |
| **Redis** | 6379 | Localhost only |

**Production URLs:**
- Frontend: `http://your-domain.com` (via Nginx port 80)
- Backend API: `http://your-domain.com/api/*` (via Nginx → 8000)
- API Docs: `http://your-domain.com/docs`

---

## Quick Reference Commands

```bash
# Update from GitLab
cd /opt/zainone-orchestrator && git pull origin main && ./update-from-git.sh

# Restart services
sudo systemctl restart zainone-backend zainone-frontend

# View logs
sudo journalctl -u zainone-backend -f

# Check status
sudo systemctl status zainone-backend zainone-frontend

# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000
```

---

**Deployment complete!** Your app is now running on RHEL 9 with continuous deployment via Git. 🎉
