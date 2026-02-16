# 🚚 Migrating NexusLog to Hostinger VPS

This guide outlines the steps to migrate NexusLog from Vercel/Neon to a self-hosted Hostinger VPS (Ubuntu).

## Prerequisites

1.  **Hostinger VPS**: Clean Ubuntu 22.04 LTS instance.
2.  **Domain**: Point `nexuslog.thinkbits.in` to VPS IP.
3.  **SSH Access**: Ensure you can SSH into your VPS.

## Step 1: VPS Setup

1.  **Update System**:
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```
2.  **Install Dependencies**:
    ```bash
    sudo apt install python3-pip python3-venv postgresql postgresql-contrib nginx git -y
    ```

## Step 2: Database Migration

1.  **Backup Neon Data**:
    *   Use `pg_dump` to export your Neon database.
    ```bash
    pg_dump "postgres://user:pass@ep-xyz.neon.tech/neondb" > backup.sql
    ```
2.  **Setup Local Postgres**:
    ```bash
    sudo -u postgres psql
    CREATE DATABASE nexuslog;
    CREATE USER nexuslog_user WITH PASSWORD 'your_password';
    GRANT ALL PRIVILEGES ON DATABASE nexuslog TO nexuslog_user;
    \q
    ```
3.  **Restore Data**:
    ```bash
    psql -U nexuslog_user -d nexuslog -f backup.sql
    ```

## Step 3: Application Deployment

1.  **Clone Repository**:
    ```bash
    cd /var/www
    git clone https://github.com/sthacker-ai/NexusLog.git nexuslog
    cd nexuslog
    ```
2.  **Backend Setup**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r backend/requirements.txt
    pip install gunicorn
    ```
3.  **Frontend Build**:
    *   *Option A*: Build locally and SCP `dist` folder to `/var/www/nexuslog/frontend/dist`.
    *   *Option B*: Install Node/NPM on VPS and build there.
    ```bash
    cd frontend
    npm install
    npm run build
    ```

## Step 4: Configure Services

1.  **Gunicorn Service (`/etc/systemd/system/nexuslog.service`)**:
    ```ini
    [Unit]
    Description=Gunicorn instance to serve NexusLog
    After=network.target

    [Service]
    User=www-data
    Group=www-data
    WorkingDirectory=/var/www/nexuslog/backend
    Environment="PATH=/var/www/nexuslog/venv/bin"
    EnvironmentFile=/var/www/nexuslog/.env
    ExecStart=/var/www/nexuslog/venv/bin/gunicorn --workers 3 --bind unix:nexuslog.sock app:app

    [Install]
    WantedBy=multi-user.target
    ```
2.  **Nginx Config (`/etc/nginx/sites-available/nexuslog`)**:
    ```nginx
    server {
        server_name nexuslog.thinkbits.in;

        location / {
            root /var/www/nexuslog/frontend/dist;
            try_files $uri $uri/ /index.html;
        }

        location /api {
            include proxy_params;
            proxy_pass http://unix:/var/www/nexuslog/backend/nexuslog.sock;
        }
    }
    ```
3.  **Enable Site**:
    ```bash
    sudo ln -s /etc/nginx/sites-available/nexuslog /etc/nginx/sites-enabled
    sudo systemctl restart nginx
    sudo systemctl start nexuslog
    sudo systemctl enable nexuslog
    ```

## Step 5: SSL (Certbot)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d nexuslog.thinkbits.in
```

## Step 6: Update Environment Variables

Update `/var/www/nexuslog/.env`:
-   `DATABASE_URL`: `postgresql://nexuslog_user:your_password@localhost/nexuslog`
-   `STORAGE_MODE`: `local` (to switch back from Vercel Blob)
-   `TELEGRAM_BOT_TOKEN`, `GOOGLE_AI_API_KEY`, etc.

## Step 7: Migration from Vercel Blob

If you used Vercel Blob, your files are still there.
-   **Option A**: Keep using Vercel Blob (requires token in `.env`).
-   **Option B**: Download all files from Blob and move to `/var/www/nexuslog/backend/static/uploads`. Update database `file_path` entries to point to local paths.
