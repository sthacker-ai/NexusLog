# 🚀 Deploying NexusLog to Vercel

This guide details how to deploy the NexusLog application to Vercel's free tier, utilizing Vercel Blob for storage and Neon Postgres for the database.

## Prerequisites

1.  **Vercel Account**: [Sign up](https://vercel.com/signup)
2.  **Neon Postgres Account**: [Sign up](https://neon.tech/) (Get `DATABASE_URL`)
3.  **Telegram Bot Token**: From [@BotFather](https://t.me/BotFather)
4.  **Google AI API Key**: [Get it here](https://aistudio.google.com/app/apikey)

## Step 1: Database Setup (Vercel Marketplace)

1.  We will use **Neon Postgres** via Vercel Marketplace (easiest method).
2.  You don't need to do this yet; you can do it during Step 2.
3.  **Note**: We will NOT copy local data. We will create a fresh schema in the cloud.

## Step 2: Vercel Project Setup

1.  Go to Vercel Dashboard -> Add New -> Project.
2.  Import your GitHub repository (`NexusLog`).
3.  **Branch Selection**:
    *   **Production Branch**: Select `vercel-hosting` (since we haven't merged to main yet).
    *   Vercel will ask "Output Directory" or "Framework Preset". Select **Vite** (default).
4.  **Environment Variables**:
    *   Skip for now, or add them if you have them ready.
5.  **Deploy**: Click Deploy. It might fail initially due to missing env vars, that's fine.

## Step 3: Add Database (Neon)

1.  In your Vercel Project Dashboard, go to **Storage**.
2.  Click **Connect Store** -> **Neon**.
3.  Follow the prompts to "Install Neon" and "Create Database".
    *   Select the **Free Plan**.
    *   Linking it to your Vercel project automatically adds `DATABASE_URL` and `POSTGRES_...` variables to your environment.


## Step 3: Environment Variables

Configure the following environment variables in Vercel (Settings -> Environment Variables):

    *   Vercel automatically sets `DATABASE_URL` when you connect Neon. You don't need to add it manually if you used the Marketplace.
    *   Add the others manually:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Your Telegram Bot Token | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `GOOGLE_AI_API_KEY` | Gemini API Key | `AIzaSy...` |
| `FLASK_ENV` | Environment mode | `production` |
| `VITE_API_URL` | Frontend API Base URL | `/api` |
| `BLOB_READ_WRITE_TOKEN` | Vercel Blob Token | (Generated in Step 4) |
| `SECRET_KEY` | Flask Session Secret | (Generate a random string) |

## Step 4: Vercel Blob Storage Setup

1.  Go to **Storage** tab.
2.  Click **Connect Store** -> **Create New** -> **Blob**.
3.  Name it `nexuslog-blob`.
4.  This adds `BLOB_READ_WRITE_TOKEN` automatically.

## Step 5: Webhook Configuration

The Telegram bot needs to know where to send updates.

1.  After deployment, you will get a URL like `https://nexuslog-git-vercel-hosting.vercel.app` (or similar).
2.  Set the webhook manually by visiting this URL in your browser:
    `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://YOUR_VERCEL_DOMAIN/api/telegram/webhook`
    
    *Replace `<YOUR_BOT_TOKEN>` and `YOUR_VERCEL_DOMAIN` accordingly.*

## Step 6: Initialize Database Schema

Your production database is empty. We need to create the tables.
We will run the initialization script **locally**, but point it to the **remote** database.

1.  Go to Vercel Dashboard -> Settings -> Environment Variables.
2.  Reveal and copy the value of `POSTGRES_URL_NO_SSL` (or `DATABASE_URL` - make sure to add `?sslmode=require` if it's missing or if connection fails).
    *   *Tip: Neon usually requires SSL.*
3.  **Locally** (in your VS Code terminal):
    *   **Windows (PowerShell)**:
        ```powershell
        $env:DATABASE_URL="postgres://user:pass@ep-xyz.neon.tech/neondb?sslmode=require"
        python backend/init_tables.py
        $env:DATABASE_URL=""  # Clear it afterwards
        ```
    *   **Mac/Linux**:
        ```bash
        export DATABASE_URL="postgres://user:pass@ep-xyz.neon.tech/neondb?sslmode=require"
        python backend/init_tables.py
        unset DATABASE_URL
        ```
4.  You should see "✅ Tables verified/created successfully."

## Step 7: Final Deploy & DNS

1.  If your initial deploy failed (due to missing vars), go to **Deployments** -> Redeploy.
2.  Test the app.
3.  **DNS (Hostinger)**:
    *   Go to Vercel Settings -> Domains.
    *   Add `nexuslog.thinkbits.in`.
    *   Vercel will give you a CNAME/A record.
    *   Add that to Hostinger DNS Zone.

## Troubleshooting

-   **404 on API**: Check `vercel.json` rewrites.
-   **Database Errors**: Ensure `DATABASE_URL` is correct and SSL is enabled (`?sslmode=require`).
-   **Bot Not Responding**: Check Vercel Function logs (Runtime Logs). Ensure Webhook is set correctly.
