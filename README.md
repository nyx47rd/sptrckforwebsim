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

## 🕒 Setting up the Cron Job

The `/tasks/update-playing` endpoint needs to be called periodically to keep all users' track data fresh. This can be configured using the **Cron Jobs** tab in your Vercel project's dashboard.

1.  Go to the **Cron Jobs** tab in your Vercel project.
2.  Create a new cron job with the following settings:
    -   **Schedule:** Choose how often you want the job to run (e.g., `*/2 * * * *` for every 2 minutes).
    -   **URL to hit:** Enter the full URL for your tasks endpoint: `https://your-project.vercel.app/tasks/update-playing`.
    -   **HTTP Method:** `POST`.
    -   **Headers:** You must add a custom header for security. The key should be `x-cron-secret` and the value should be the `CRON_SECRET` you set in your environment variables.

This will trigger the batch update process periodically.
