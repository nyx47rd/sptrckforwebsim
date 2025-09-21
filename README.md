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

### Step 4: Configure Environment Variables

In your Vercel project's settings ("Settings" -> "Environment Variables"), create the following variables one by one and enter their values:

| Variable Name              | Description                                                                                                                  | Example Value                                |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `SPOTIFY_CLIENT_ID`        | The Client ID from your Spotify Developer Dashboard.                                                                         | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`           |
| `SPOTIFY_CLIENT_SECRET`    | The Client Secret from your Spotify Developer Dashboard.                                                                     | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`           |
| `SPOTIFY_REDIRECT_URI`     | The Redirect URI you added to your Spotify settings.                                                                         | `https://your-project.vercel.app/auth/callback` |
| `DATABASE_URL`             | The PostgreSQL connection URL from Vercel or another provider.                                                               | `postgres://...`                             |
| `MY_SPOTIFY_REFRESH_TOKEN` | Your personal Spotify refresh token to be used for the "Now Playing" widget. (You will obtain this in the next step).         | `AQ...`                                      |
| `CRON_SECRET`              | A secret key to trigger the scheduled task. Use a complex, unpredictable string.                                             | `a-very-secure-and-random-key-for-cron`      |

### Step 5: Generate Your Personal Refresh Token

To get the personal "Now Playing" widget (`/api/now-playing`) working, you need to obtain a `refresh_token` for your own Spotify account.

1.  Make sure you have cloned the project files and installed the packages from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
2.  Create a `.env` file in the project's root directory and fill in the variables from above (especially `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`) for your local setup.
3.  Run the following command in your terminal:
    ```bash
    python generate_token.py
    ```
4.  Follow the steps provided by the script. Go to the URL it gives you, authorize the app, and paste the final redirected URL back into the terminal.
5.  The script will give you a `Refresh Token`. Copy this token and paste it as the value for the `MY_SPOTIFY_REFRESH_TOKEN` environment variable in Vercel.

### Step 6: Deploy the Project

Vercel will automatically deploy any changes to your repository's `main` branch. After setting the environment variables, you can trigger a new deployment from the Vercel dashboard.

---

## 💻 Usage

-   **Login:** Go to `https://your-project.vercel.app/auth/login` to log in with your Spotify account.
-   **Start/Stop Sharing:** API endpoints (`/share/start`, `/share/stop`) are available for this feature. You can build a UI to interact with them.
-   **View Feed:** Get a JSON list of all users currently sharing their tracks at `https://your-project.vercel.app/feed`.
-   **Personal Widget:** Get your own currently playing data from `https://your-project.vercel.app/api/now-playing`.

## 🕒 Setting up the Cron Job

The `/tasks/update-playing` endpoint needs to be called periodically to keep the track data fresh. You can do this with Vercel's native "Cron Jobs" feature.

1.  Add a `vercel.json` file to your project's root directory (it's already included in this repo).
2.  Add a definition like the one below to the `crons` section:
    ```json
    {
      "crons": [
        {
          "path": "/tasks/update-playing",
          "schedule": "*/2 * * * *"
        }
      ]
    }
    ```
    This example runs the task every 2 minutes. You can change the `schedule` value as you see fit. Remember that you must send the `x-cron-secret` header with the correct value when calling this endpoint. You can add custom headers in the Vercel Cron Job settings.
