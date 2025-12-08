#!/bin/bash

# ZainOne Orchestrator Studio - RHEL9 Production Deployment Script
# This script automates the deployment process for RHEL9 servers

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
APP_NAME="zainone-orchestrator-studio"
APP_USER="zainone"
DB_NAME="zainone_orchestrator"
DB_USER="zainone_user"
DOMAIN_NAME=""
SSL_EMAIL=""
GITHUB_REPO="https://github.com/your-repo/zainone-orchestrator-studio.git"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
}

get_user_input() {
    log_info "Please provide the following information for deployment:"

    read -p "Domain name (e.g., your-domain.com): " DOMAIN_NAME
    if [[ -z "$DOMAIN_NAME" ]]; then
        log_error "Domain name is required"
        exit 1
    fi

    read -p "SSL certificate email for Let's Encrypt: " SSL_EMAIL
    if [[ -z "$SSL_EMAIL" ]]; then
        log_warning "SSL email not provided. SSL will not be configured automatically."
    fi

    read -s -p "Database password for $DB_USER: " DB_PASSWORD
    echo
    if [[ -z "$DB_PASSWORD" ]]; then
        log_error "Database password is required"
        exit 1
    fi

    read -s -p "Application secret key (press enter for auto-generated): " SECRET_KEY
    echo
    if [[ -z "$SECRET_KEY" ]]; then
        SECRET_KEY=$(openssl rand -hex 32)
        log_info "Generated secret key: $SECRET_KEY"
    fi
}

update_system() {
    log_info "Updating system packages..."
    dnf update -y
    dnf install -y epel-release
    log_success "System updated"
}

install_dependencies() {
    log_info "Installing system dependencies..."

    # Development tools
    dnf groupinstall -y "Development Tools"
    dnf install -y wget curl git vim

    # Python 3.9+
    dnf config-manager --set-enabled crb
    dnf install -y python39 python39-pip python39-devel
    ln -sf /usr/bin/python3.9 /usr/bin/python3
    ln -sf /usr/bin/pip3.9 /usr/bin/pip3

    # Node.js 16+
    curl -fsSL https://rpm.nodesource.com/setup_16.x | bash -
    dnf install -y nodejs

    # PostgreSQL
    dnf install -y postgresql-server postgresql-contrib postgresql-devel
    postgresql-setup initdb
    systemctl start postgresql
    systemctl enable postgresql

    # Redis (optional)
    dnf install -y redis
    systemctl start redis
    systemctl enable redis

    # Nginx
    dnf install -y nginx
    systemctl start nginx
    systemctl enable nginx

    # Certbot for SSL
    if [[ -n "$SSL_EMAIL" ]]; then
        dnf install -y certbot python3-certbot-nginx
    fi

    log_success "Dependencies installed"
}

setup_database() {
    log_info "Setting up PostgreSQL database..."

    # Create database and user
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || log_warning "Database $DB_NAME may already exist"
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';" 2>/dev/null || log_warning "User $DB_USER may already exist"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"

    # Configure authentication
    PG_HBA="/var/lib/pgsql/data/pg_hba.conf"
    if ! grep -q "$DB_NAME" "$PG_HBA"; then
        sed -i "/^local.*all.*all.*peer/a local   $DB_NAME   $DB_USER                           md5" "$PG_HBA"
    fi

    systemctl restart postgresql

    log_success "Database setup completed"
}

create_app_user() {
    log_info "Creating application user..."

    useradd -m -s /bin/bash "$APP_USER" 2>/dev/null || log_warning "User $APP_USER may already exist"
    usermod -aG wheel "$APP_USER"

    log_success "Application user created"
}

deploy_application() {
    log_info "Deploying application..."

    # Clone repository
    if [[ ! -d "/home/$APP_USER/$APP_NAME" ]]; then
        sudo -u "$APP_USER" git clone "$GITHUB_REPO" "/home/$APP_USER/$APP_NAME"
    else
        log_warning "Application directory already exists. Pulling latest changes..."
        sudo -u "$APP_USER" bash -c "cd /home/$APP_USER/$APP_NAME && git pull"
    fi

    cd "/home/$APP_USER/$APP_NAME"

    # Backend setup
    log_info "Setting up backend..."
    cd backend
    sudo -u "$APP_USER" python3 -m venv venv
    sudo -u "$APP_USER" bash -c "source venv/bin/activate && pip install --upgrade pip"
    sudo -u "$APP_USER" bash -c "source venv/bin/activate && pip install -r requirements.txt"

    # Create .env file
    cat > .env << EOF
# Database
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME

# Redis
REDIS_URL=redis://localhost:6379

# Application
APP_ENV=production
DEBUG=False
SECRET_KEY=$SECRET_KEY

# Server
HOST=127.0.0.1
PORT=8000

# LLM Configuration (configure as needed)
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-llm-api-key-here

# Security
JWT_SECRET_KEY=$SECRET_KEY
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF

    # Initialize database
    sudo -u "$APP_USER" bash -c "source venv/bin/activate && python -m app.db.init_db"

    # Frontend setup
    log_info "Setting up frontend..."
    cd ../frontend
    sudo -u "$APP_USER" npm install
    sudo -u "$APP_USER" npm run build

    # Install serve globally
    npm install -g serve

    log_success "Application deployed"
}

create_systemd_services() {
    log_info "Creating systemd services..."

    # Backend service
    cat > /etc/systemd/system/zainone-backend.service << EOF
[Unit]
Description=ZainOne Orchestrator Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=/home/$APP_USER/$APP_NAME/backend
Environment=PATH=/home/$APP_USER/$APP_NAME/backend/venv/bin
ExecStart=/home/$APP_USER/$APP_NAME/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # Frontend service
    cat > /etc/systemd/system/zainone-frontend.service << EOF
[Unit]
Description=ZainOne Orchestrator Frontend
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=/home/$APP_USER/$APP_NAME/frontend
ExecStart=/usr/bin/serve -s build -l 3000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable zainone-backend
    systemctl enable zainone-frontend

    log_success "Systemd services created"
}

configure_nginx() {
    log_info "Configuring Nginx..."

    cat > /etc/nginx/conf.d/zainone.conf << EOF
# Upstream backend servers
upstream zainone_backend {
    server 127.0.0.1:8000;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;

    # SSL configuration (will be updated by certbot)
    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;
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
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://zainone_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;

        # API specific settings
        client_max_body_size 50M;
    }

    # Static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # Remove default nginx config
    rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

    nginx -t
    systemctl reload nginx

    log_success "Nginx configured"
}

setup_ssl() {
    if [[ -n "$SSL_EMAIL" ]]; then
        log_info "Setting up SSL certificates with Let's Encrypt..."

        certbot --nginx -d "$DOMAIN_NAME" -d "www.$DOMAIN_NAME" --email "$SSL_EMAIL" --agree-tos --non-interactive

        log_success "SSL certificates configured"
    else
        log_warning "SSL email not provided. Skipping automatic SSL setup."
        log_info "You can manually configure SSL later or run: certbot --nginx -d $DOMAIN_NAME"
    fi
}

configure_firewall() {
    log_info "Configuring firewall..."

    dnf install -y firewalld
    systemctl start firewalld
    systemctl enable firewalld

    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload

    log_success "Firewall configured"
}

start_services() {
    log_info "Starting services..."

    systemctl start zainone-backend
    systemctl start zainone-frontend

    log_success "Services started"
}

create_backup_script() {
    log_info "Creating backup script..."

    cat > /usr/local/bin/backup-zainone.sh << EOF
#!/bin/bash
BACKUP_DIR="/home/$APP_USER/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
DB_NAME="$DB_NAME"
DB_USER="$DB_USER"

mkdir -p \$BACKUP_DIR

# Database backup
pg_dump -U \$DB_USER -h localhost \$DB_NAME > \$BACKUP_DIR/\${DB_NAME}_\${DATE}.sql

# Application files backup
tar -czf \$BACKUP_DIR/app_\${DATE}.tar.gz /home/$APP_USER/$APP_NAME

# Keep only last 7 days
find \$BACKUP_DIR -name "*.sql" -mtime +7 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: \$DATE"
EOF

    chmod +x /usr/local/bin/backup-zainone.sh

    # Add to cron for daily backups at 2 AM
    crontab -l 2>/dev/null | { cat; echo "0 2 * * * /usr/local/bin/backup-zainone.sh"; } | crontab -

    log_success "Backup script created and scheduled"
}

verify_deployment() {
    log_info "Verifying deployment..."

    # Check service status
    if systemctl is-active --quiet zainone-backend; then
        log_success "Backend service is running"
    else
        log_error "Backend service is not running"
    fi

    if systemctl is-active --quiet zainone-frontend; then
        log_success "Frontend service is running"
    else
        log_error "Frontend service is not running"
    fi

    if systemctl is-active --quiet nginx; then
        log_success "Nginx is running"
    else
        log_error "Nginx is not running"
    fi

    # Test connectivity (if domain is accessible)
    if curl -k -s --head "https://$DOMAIN_NAME" > /dev/null 2>&1; then
        log_success "Application is accessible at https://$DOMAIN_NAME"
    else
        log_warning "Could not verify application accessibility. Check network/firewall settings."
    fi
}

print_completion_message() {
    log_success "Deployment completed successfully!"
    echo
    echo "=================================================================="
    echo "ZainOne Orchestrator Studio has been deployed to RHEL9"
    echo "=================================================================="
    echo
    echo "Application URLs:"
    echo "  Frontend: https://$DOMAIN_NAME"
    echo "  API Docs:  https://$DOMAIN_NAME/docs"
    echo
    echo "Service Management:"
    echo "  Start services:   systemctl start zainone-backend zainone-frontend"
    echo "  Stop services:    systemctl stop zainone-backend zainone-frontend"
    echo "  Restart services: systemctl restart zainone-backend zainone-frontend"
    echo "  View logs:        journalctl -u zainone-backend -f"
    echo
    echo "Backup:"
    echo "  Manual backup: /usr/local/bin/backup-zainone.sh"
    echo "  Automatic daily backups at 2 AM"
    echo
    echo "Next Steps:"
    echo "1. Configure your LLM API keys in /home/$APP_USER/$APP_NAME/backend/.env"
    echo "2. Update application settings as needed"
    echo "3. Test the application functionality"
    echo "4. Monitor logs for any issues"
    echo
    echo "=================================================================="
}

# Main execution
main() {
    log_info "Starting ZainOne Orchestrator Studio deployment on RHEL9"

    check_root
    get_user_input

    update_system
    install_dependencies
    setup_database
    create_app_user
    deploy_application
    create_systemd_services
    configure_nginx
    setup_ssl
    configure_firewall
    start_services
    create_backup_script
    verify_deployment

    print_completion_message
}

# Run main function
main "$@"
