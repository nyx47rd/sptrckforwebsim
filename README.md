# Spotify Track Sharer with Admin Controls

This project is a multi-user web application that allows users to share their currently playing Spotify track. It includes a private admin panel for the site owner to manage settings, such as the public visibility of the feed.

## ✨ Features

-   **Multi-User Platform:** Any user can log in with their Spotify account to start sharing their "Now Playing" status.
-   **Admin Panel:** The first user to sign up automatically becomes the admin, able to access a private admin panel.
-   **Public Feed Control:** The admin can enable or disable the public visibility of the shared tracks feed.
-   **Personal "Now Playing" Widget:** A separate, single-user API endpoint is available for the owner to embed their own "Now Playing" status on a personal website.
-   **Scalable Background Updates:** A robust, batch-processing cron job updates user statuses without timing out in a serverless environment.
-   **Easy Deployment:** Designed for Vercel with a PostgreSQL database.

## 🛠️ Tech Stack

-   **Backend:** [FastAPI](https://fastapi.tiangolo.com/)
-   **Database:** [SQLAlchemy](https://www.sqlalchemy.org/) ORM with PostgreSQL.
-   **Deployment:** [Vercel](https://vercel.com/)

---

## 🚀 Setup and Deployment Guide

### Step 1: Fork & Clone
Fork this repository and clone it to your local machine.

### Step 2: Create a Spotify Developer App
1.  Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) and create a new app.
2.  Note your **Client ID** and **Client Secret**.
3.  Click "Edit Settings" and add your deployment's callback URL to the "Redirect URIs".
    -   Example for production: `https://your-project.vercel.app/auth/callback`

### Step 3: Create a Vercel Project and Database
1.  Create a new Vercel project and link your forked GitHub repository.
2.  Go to the "Storage" tab and create a new **Postgres** database.
3.  Copy the **`DATABASE_URL`** connection string.

### Step 4: Create the Database Schema
1.  In your Neon (or other PostgreSQL provider) dashboard, find the **SQL Editor**.
2.  Copy and run the entire SQL script below to create the necessary tables.
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    spotify_id VARCHAR NOT NULL UNIQUE,
    display_name VARCHAR,
    profile_pic_url VARCHAR,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX ix_users_spotify_id ON users (spotify_id);

CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    access_token VARCHAR NOT NULL,
    refresh_token VARCHAR NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

CREATE TABLE tracks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    track_name VARCHAR,
    artist_name VARCHAR,
    album_cover_url VARCHAR,
    spotify_track_url VARCHAR,
    currently_playing BOOLEAN DEFAULT FALSE
);

CREATE TABLE active_shares (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    expires_at TIMESTAMP
);

CREATE TABLE settings (
    key VARCHAR PRIMARY KEY,
    value VARCHAR
);
CREATE INDEX ix_settings_key ON settings (key);

-- Add a default setting for the feed's public visibility
INSERT INTO settings (key, value) VALUES ('feed_is_public', 'true');
```

### Step 5: Configure Environment Variables
In your Vercel project's "Settings" -> "Environment Variables", add the following:

| Variable Name              | Description                                                                    |
| -------------------------- | ------------------------------------------------------------------------------ |
| `SPOTIFY_CLIENT_ID`        | From your Spotify App.                                                         |
| `SPOTIFY_CLIENT_SECRET`    | From your Spotify App.                                                         |
| `SPOTIFY_REDIRECT_URI`     | The full callback URL for your Vercel deployment.                              |
| `DATABASE_URL`             | The connection URL for your Postgres database.                                 |
| `MY_SPOTIFY_REFRESH_TOKEN` | Your personal refresh token for the widget. (Get this in the next step).         |
| `CRON_SECRET`              | A long, random string to secure the cron job endpoint.                         |
| `ADMIN_PASSWORD`           | A password you choose for the admin panel.                                     |


### Step 6: Deploy and Become Admin
1.  Push your code to GitHub to trigger a Vercel deployment.
2.  Once deployed, go to `https://your-project.vercel.app/auth/login`.
3.  **Log in with your own Spotify account.** As the first user to sign up, you will automatically be made the admin.
4.  The page will show you an `access_token` and `refresh_token`.
5.  Copy the `refresh_token` and set it as the `MY_SPOTIFY_REFRESH_TOKEN` environment variable in Vercel. This will activate your personal widget.
6.  Keep the `access_token` handy to use the admin panel.

---

## 🔒 Admin Panel

-   **Access:** Go to `https://your-project.vercel.app/admin.html`.
-   **Authentication:** Paste the `access_token` you received after logging in to access the settings.
-   **Features:** You can toggle the public visibility of the `/feed` endpoint.

## 💻 Usage

-   **Login:** `https://your-project.vercel.app/auth/login`
-   **Personal Widget API:** `https://your-project.vercel.app/api/now-playing`
-   **Public Feed:** `https://your-project.vercel.app/feed` (if enabled in admin panel)

## 🕒 Setting up the Cron Job
Use the **Cron Jobs** tab in your Vercel project dashboard to periodically call the `POST https://your-project.vercel.app/tasks/update-playing` endpoint. Remember to add the `x-cron-secret` header with the value you set. A schedule of `*/2 * * * *` (every 2 minutes) is a good starting point.
