# ZainOne Orchestrator Studio - Production Deployment on RHEL9

This guide provides comprehensive instructions for deploying the ZainOne Orchestrator Studio to a production RHEL9 server.

## Prerequisites

### System Requirements
- RHEL9 server with root or sudo access
- Minimum 4GB RAM, 2 CPU cores
- 20GB free disk space
- Network connectivity

### Required Software
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis (optional, for caching)
- Nginx
- Git

## 1. System Preparation

### Update System
```bash
sudo dnf update -y
sudo dnf install -y epel-release
```

### Install Development Tools
```bash
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y wget curl git vim
```

### Install Python 3.9+
```bash
# Enable CodeReady Builder repository
sudo dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm
sudo dnf config-manager --set-enabled crb

# Install Python 3.9
sudo dnf install -y python39 python39-pip python39-devel

# Create symbolic links
sudo ln -sf /usr/bin/python3.9 /usr/bin/python3
sudo ln -sf /usr/bin/pip3.9 /usr/bin/pip3
```

### Install Node.js 16+
```bash
# Install Node.js 16.x
curl -fsSL https://rpm.nodesource.com/setup_16.x | sudo bash -
sudo dnf install -y nodejs
```

### Install PostgreSQL
```bash
# Install PostgreSQL
sudo dnf install -y postgresql-server postgresql-contrib postgresql-devel

# Initialize database
sudo postgresql-setup initdb

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Install Redis (Optional)
```bash
sudo dnf install -y redis
sudo systemctl start redis
sudo systemctl enable redis
```

### Install Nginx
```bash
sudo dnf install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

## 2. Database Setup

### Configure PostgreSQL
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE zainone_orchestrator;
CREATE USER zainone_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE zainone_orchestrator TO zainone_user;
ALTER USER zainone_user CREATEDB;
\q
```

### Configure PostgreSQL Authentication
```bash
sudo vim /var/lib/pgsql/data/pg_hba.conf
```

Add the following line before the existing local connections:
```
local   zainone_orchestrator   zainone_user                           md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

## 3. Application Deployment

### Create Application User
```bash
sudo useradd -m -s /bin/bash zainone
sudo usermod -aG wheel zainone
```

### Clone Repository
```bash
sudo -u zainone bash
cd ~
git clone https://github.com/your-repo/zainone-orchestrator-studio.git
cd zainone-orchestrator-studio
```

### Backend Setup

#### Create Virtual Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Configure Environment
```bash
cp .env.example .env
vim .env
```

Update .env with production settings:
```bash
# Database
DATABASE_URL=postgresql://zainone_user:your_secure_password@localhost/zainone_orchestrator

# Redis (if installed)
REDIS_URL=redis://localhost:6379

# Application
APP_ENV=production
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here

# Server
HOST=127.0.0.1
PORT=8000

# LLM Configuration
LLM_BASE_URL=https://your-llm-endpoint
LLM_API_KEY=your-llm-api-key

# Security
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### Initialize Database
```bash
python -m app.db.init_db
```

### Frontend Setup

#### Install Dependencies
```bash
cd ../frontend
npm install
```

#### Build Production Bundle
```bash
npm run build
```

## 4. Production Services Configuration

### Backend Systemd Service

Create systemd service file:
```bash
sudo vim /etc/systemd/system/zainone-backend.service
```

Content:
```ini
[Unit]
Description=ZainOne Orchestrator Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=zainone
WorkingDirectory=/home/zainone/zainone-orchestrator-studio/backend
Environment=PATH=/home/zainone/zainone-orchestrator-studio/backend/venv/bin
ExecStart=/home/zainone/zainone-orchestrator-studio/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Frontend Systemd Service

Create systemd service file:
```bash
sudo vim /etc/systemd/system/zainone-frontend.service
```

Content:
```ini
[Unit]
Description=ZainOne Orchestrator Frontend
After=network.target

[Service]
Type=simple
User=zainone
WorkingDirectory=/home/zainone/zainone-orchestrator-studio/frontend
ExecStart=/usr/bin/serve -s build -l 3000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Install serve globally for frontend
```bash
sudo npm install -g serve
```

### Enable and Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable zainone-backend
sudo systemctl enable zainone-frontend
sudo systemctl start zainone-backend
sudo systemctl start zainone-frontend
```

## 5. Nginx Reverse Proxy Configuration

### Configure Nginx
```bash
sudo vim /etc/nginx/conf.d/zainone.conf
```

Content:
```nginx
# Upstream backend servers
upstream zainone_backend {
    server 127.0.0.1:8000;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://zainone_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # API specific settings
        client_max_body_size 50M;
    }

    # Static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Remove default nginx configuration
```bash
sudo rm /etc/nginx/sites-enabled/default
```

### Test Nginx Configuration
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 6. SSL/TLS Certificate Setup

### Using Let's Encrypt (Recommended)
```bash
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Manual Certificate Installation
Place your certificates in:
- `/etc/ssl/certs/your-domain.crt`
- `/etc/ssl/private/your-domain.key`

## 7. Security Hardening

### Firewall Configuration
```bash
sudo dnf install -y firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld

# Allow HTTP and HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### SELinux Configuration
```bash
# Check SELinux status
sestatus

# If enforcing, adjust policies as needed
sudo setsebool -P httpd_can_network_connect 1
```

### Secure SSH
```bash
sudo vim /etc/ssh/sshd_config
```

Update settings:
```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

## 8. Monitoring and Logging

### Install Monitoring Tools
```bash
sudo dnf install -y htop iotop sysstat
```

### Configure Log Rotation
```bash
sudo vim /etc/logrotate.d/zainone
```

Content:
```
/home/zainone/zainone-orchestrator-studio/backend/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 zainone zainone
    postrotate
        systemctl reload zainone-backend
    endscript
}
```

### System Monitoring
```bash
# Enable sysstat
sudo systemctl enable sysstat
sudo systemctl start sysstat
```

## 9. Backup Strategy

### Database Backup Script
```bash
sudo vim /usr/local/bin/backup-zainone.sh
```

Content:
```bash
#!/bin/bash
BACKUP_DIR="/home/zainone/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="zainone_orchestrator"
DB_USER="zainone_user"

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_DIR/${DB_NAME}_${DATE}.sql

# Application files backup
tar -czf $BACKUP_DIR/app_${DATE}.tar.gz /home/zainone/zainone-orchestrator-studio

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable:
```bash
sudo chmod +x /usr/local/bin/backup-zainone.sh
```

### Schedule Backups
```bash
sudo crontab -e
```

Add line for daily backup at 2 AM:
```
0 2 * * * /usr/local/bin/backup-zainone.sh
```

## 10. Performance Optimization

### Database Optimization
```bash
sudo -u postgres psql -d zainone_orchestrator
```

Run optimizations:
```sql
-- Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_conversation_user_id ON conversations(user_id);
CREATE INDEX CONCURRENTLY idx_message_conversation_id ON messages(conversation_id);

-- Analyze tables
ANALYZE;
```

### Application Optimization
Update .env with production settings:
```bash
# Performance settings
WORKERS=4
WORKER_CLASS=uvicorn.workers.UvicornWorker
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=50
```

## 11. Deployment Verification

### Health Checks
```bash
# Check services status
sudo systemctl status zainone-backend
sudo systemctl status zainone-frontend
sudo systemctl status nginx
sudo systemctl status postgresql

# Test API endpoint
curl -k https://your-domain.com/api/health

# Test frontend
curl -k https://your-domain.com
```

### Logs Monitoring
```bash
# Backend logs
sudo journalctl -u zainone-backend -f

# Frontend logs
sudo journalctl -u zainone-frontend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 12. Troubleshooting

### Common Issues

1. **Port conflicts**: Check if ports 80, 443, 8000, 3000 are available
2. **Permission issues**: Ensure zainone user has proper permissions
3. **Database connection**: Verify PostgreSQL credentials and connectivity
4. **SSL issues**: Check certificate paths and permissions
5. **Firewall blocking**: Verify firewalld rules

### Log Locations
- Backend: `journalctl -u zainone-backend`
- Frontend: `journalctl -u zainone-frontend`
- Nginx: `/var/log/nginx/`
- PostgreSQL: `/var/log/postgresql/`

## 13. Maintenance Commands

### Update Application
```bash
sudo -u zainone bash
cd ~/zainone-orchestrator-studio

# Backend update
cd backend
source venv/bin/activate
git pull
pip install -r requirements.txt --upgrade
sudo systemctl restart zainone-backend

# Frontend update
cd ../frontend
git pull
npm install
npm run build
sudo systemctl restart zainone-frontend
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u zainone-backend -f
sudo journalctl -u zainone-frontend -f

# Recent logs
sudo journalctl -u zainone-backend --since "1 hour ago"
```

### Restart Services
```bash
sudo systemctl restart zainone-backend
sudo systemctl restart zainone-frontend
sudo systemctl reload nginx
```

This deployment guide ensures a secure, scalable, and maintainable production environment for the ZainOne Orchestrator Studio on RHEL9.
