# Spotify Track Sharer & Now Playing Widget

This project is a web application that allows users to share the song they are currently listening to on Spotify with their friends, and an API that provides a personal "Now Playing" widget. It is built with FastAPI and designed for deployment on Vercel.

## ✨ Features

-   **Multi-User Sharing:** Users can log in with their Spotify accounts and share the song they are currently listening to on a public feed.
-   **Personal "Now Playing" Widget:** The `/api/now-playing` endpoint provides a data output showing the song you are currently listening to, which you can embed on your own website or profile.
-   **Automatic Updates:** A background task (cron job) periodically updates the currently playing tracks for all active users.
-   **Easy Deployment:** Designed for easy deployment with Vercel and a cloud database provider (e.g., Vercel Postgres).

## 🛠️ Tech Stack

-   **Backend:** [FastAPI](https://fastapi.tiangolo.com/)
-   **Database:** [SQLAlchemy](https://www.sqlalchemy.org/) ORM with PostgreSQL (production) and SQLite (local development).
-   **Deployment:** [Vercel](https://vercel.com/)
-   **Spotify Integration:** [Spotify Web API](https://developer.spotify.com/documentation/web-api)

---

## 🚀 Setup and Deployment Guide

Follow these steps to run this project on your own Vercel account.

### Step 1: Fork & Clone the Project

1.  **Fork** this GitHub repository to your own account.
2.  Clone your forked repository to your local machine:
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_PROJECT_NAME.git
    cd YOUR_PROJECT_NAME
    ```

### Step 2: Create a Spotify Developer Application

1.  Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) and log in.
2.  Click the **"Create App"** button to create a new application.
3.  After creating your app, take note of the **"Client ID"** and **"Client Secret"**. You can view the secret by clicking "Show client secret".
4.  Click the **"Edit Settings"** button.
5.  In the **"Redirect URIs"** section, add the URL of your Vercel application followed by the `/auth/callback` path. For example:
    -   `https://your-project.vercel.app/auth/callback`
    -   For local development: `http://127.0.0.1:8000/auth/callback`
6.  Save the settings.

### Step 3: Create a Vercel Project and Database

1.  **Log in to Vercel:** Log in to your [Vercel](https://vercel.com/) account.
2.  **Create a New Project:** Go to "Add New... -> Project", and select the repository you forked on GitHub.
3.  **Create a Database:** On the project page, go to the "Storage" tab and create a new database with the "Postgres" option. After the database is created, you will be given a **`DATABASE_URL`**. Copy this URL.

### Step 4: Create the Database Schema

Before running the application, you need to create the necessary tables in your database.

1.  Connect to your Neon (or other PostgreSQL) database.
2.  Go to the **SQL Editor**.
3.  Copy the entire SQL code below and run it. This will create all the tables the application needs.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    spotify_id VARCHAR NOT NULL,
    display_name VARCHAR,
    profile_pic_url VARCHAR,
    UNIQUE (spotify_id)
);

CREATE INDEX ix_users_id ON users (id);
CREATE INDEX ix_users_spotify_id ON users (spotify_id);

CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    access_token VARCHAR NOT NULL,
    refresh_token VARCHAR NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_tokens_id ON tokens (id);

CREATE TABLE tracks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    track_name VARCHAR,
    artist_name VARCHAR,
    album_cover_url VARCHAR,
    spotify_track_url VARCHAR,
    currently_playing BOOLEAN DEFAULT false,
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_tracks_id ON tracks (id);

CREATE TABLE active_shares (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expires_at TIMESTAMP,
    UNIQUE (user_id),
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_active_shares_id ON active_shares (id);
```

### Step 5: Configure Environment Variables

In your Vercel project's settings ("Settings" -> "Environment Variables"), create the following variables one by one and enter their values:

| Variable Name              | Description                                                                                                                  | Example Value                                |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `SPOTIFY_CLIENT_ID`        | The Client ID from your Spotify Developer Dashboard.                                                                         | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`           |
| `SPOTIFY_CLIENT_SECRET`    | The Client Secret from your Spotify Developer Dashboard.                                                                     | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`           |
| `SPOTIFY_REDIRECT_URI`     | The Redirect URI you added to your Spotify settings.                                                                         | `https://your-project.vercel.app/auth/callback` |
| `DATABASE_URL`             | The PostgreSQL connection URL from Vercel or another provider (If you choose a provider from Vercel, this information will automatically be added to the Environment Variables section)                                                             | `postgres://...`                             |
| `MY_SPOTIFY_REFRESH_TOKEN` | Your personal Spotify refresh token to be used for the "Now Playing" widget. (You will obtain this in the next step).         | `AQ...`                                      |

### Step 5: Generate Your Personal Refresh Token

To get the personal "Now Playing" widget (`/api/now-playing`) working, you need to obtain a `refresh_token` for your own Spotify account. You can get this directly from the application's authentication flow.

1.  **Deploy the Application:** Make sure your application is successfully deployed on Vercel with all the necessary environment variables from Step 4 (except `MY_SPOTIFY_REFRESH_TOKEN`, which you are about to get).

2.  **Log In Through Your Deployed App:**
    -   Go to your live application's login page: `https://your-project.vercel.app/auth/login`.
    -   Click the "Login with Spotify" button.
    -   Log in with your **personal** Spotify account that you want to display on the widget.
    -   Grant the necessary permissions.

3.  **Copy Your Refresh Token:**
    -   After you grant permissions, you will be redirected to a page that displays a JSON response.
    -   This response contains your tokens. Find the `refresh_token` field and copy its value (it will be a long string).

4.  **Set the Environment Variable:**
    -   Go back to your Vercel project settings ("Settings" -> "Environment Variables").
    -   Create a new environment variable named `MY_SPOTIFY_REFRESH_TOKEN`.
    -   Paste the `refresh_token` you copied as the value.
    -   Save the variable. Vercel will trigger a new deployment with this new variable.

After the new deployment is complete, your `/api/now-playing` widget will be active.

### Step 6: Deploy the Project

Vercel will automatically deploy any changes to your repository's `main` branch. After setting the environment variables, you can trigger a new deployment from the Vercel dashboard.

---

## 💻 Usage

-   **Login:** Go to `https://your-project.vercel.app/auth/login` to see the login page. Clicking the button will start the authorization flow.
-   **Start/Stop Sharing:** API endpoints (`/share/start`, `/share/stop`) are available for this feature. You can build a UI to interact with them.
-   **Personal Widget:** Get your own currently playing data from `https://your-project.vercel.app/api/now-playing`.
