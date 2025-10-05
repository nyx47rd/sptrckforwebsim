# Spotify Track Sharer & Now Playing Widget

This project is a web application that allows users to share the song they are currently listening to on Spotify with their friends, and an API that provides a personal "Now Playing" widget. It is built with FastAPI and designed for deployment on Vercel.

## ✨ Features

-   **Multi-User Sharing:** Users can log in and share with others what they are currently listening to.
-   **Personal "Now Playing" Widget:** Thanks to this widget, when you go to `https://your-vercel-app-name.vercel.app/public/widget.html` you will see a widget showing the currently playing song. You can embed this widget on a website if you want.
-   **Automatic Updates:** A background task periodically updates the currently playing tracks for all active users.
-   **Easy Deployment:** Designed for easy deployment with Vercel and a cloud database provider (e.g., Neon).

## 🛠️ Tech Stack

-   **Backend:** [FastAPI](https://fastapi.tiangolo.com/)
-   **Database:** [SQLAlchemy](https://www.sqlalchemy.org/) ORM with PostgreSQL (production) and SQLite (local development).
-   **Deployment:** [Vercel](https://vercel.com/)
-   **Spotify Integration:** [Spotify Web API](https://developer.spotify.com/documentation/web-api)

---

## 🚀 Setup and Deployment Guide

Follow these steps to run this project on your own Vercel account.

### Step 1: Fork & Clone the Project

1.  **Fork** or **Use this template > Create a new repository** this GitHub repository to your own account.
2.  Clone your forked repository to your local machine (**optional**):
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
3.  **Create a Database:** On the project page, go to the "Storage" tab and create a new database with the "Postgres" option. After the database is created, you will be given a **`DATABASE_URL`**. Copy this URL. If you prefer, you can have these variables created automatically by choosing an easier provider like Neon.

### Step 4: Configure Environment Variables

In your Vercel project's settings ("Settings" -> "Environment Variables"), create the following variables one by one and enter their values:

| Variable Name              | Description                                                                                                                  | Example Value                                |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `SPOTIFY_CLIENT_ID`        | The Client ID from your Spotify Developer Dashboard.                                                                         | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`           |
| `SPOTIFY_CLIENT_SECRET`    | The Client Secret from your Spotify Developer Dashboard.                                                                     | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`           |
| `SPOTIFY_REDIRECT_URI`     | The Redirect URI you added to your Spotify settings.                                                                         | `https://your-project.vercel.app/auth/callback` |
| `DATABASE_URL`             | The PostgreSQL connection URL from Vercel or another provider (If you choose a provider from Vercel, this information will automatically be added to the Environment Variables section)                                                             | `postgres://...`                             |
| `MY_SPOTIFY_REFRESH_TOKEN` | Your personal Spotify refresh token to be used for the "Now Playing" widget. (You will obtain this in the next step).         | `AQ...`                                      |

### Step 5: Generate Your Personal Refresh Token

To get the personal "Now Playing" widget (`/public/widget.html`) working, you need to obtain a `refresh_token` for your own Spotify account. You can get this directly from the application's authentication flow.

1.  **Add a new Redirect URI to your Spotify App:**
    -   Go to your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) and select your app.
    -   Click "Edit Settings".
    -   Add `https://example.com/callback` to your list of Redirect URIs and save.

2.  **Prepare your local environment:**
    -   Make sure you have cloned the project and installed dependencies (`pip install -r requirements.txt`).
    -   Create a `.env` file in the project's root directory.
    -   Fill in `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` from your dashboard. The script does not require any other variables.

3.  **Run the script:**
    -   Run the following command in your terminal:
        ```bash
        python generate_token.py
        ```
    -   The script will give you a URL. Open it, log in, and grant permissions.
    -   You will be redirected to an `example.com` page that doesn't exist. This is expected. Copy the full URL from your browser's address bar.
    -   Paste the URL back into your terminal when prompted.

4.  **Set the Environment Variable:**
    -   Go back to your Vercel project settings ("Settings" -> "Environment Variables").
    -   Create a new environment variable named `MY_SPOTIFY_REFRESH_TOKEN`.
    -   Paste the `refresh_token` you copied as the value.
    -   Save the variable. Vercel will trigger a new deployment with this new variable.

### Step 6: Deploy the Project

Vercel will automatically deploy any changes to your repository's `main` branch. After setting the environment variables, you can trigger a new deployment from the Vercel dashboard.

---

## 💻 Usage

-   **Login:** Go to `https://your-project.vercel.app/auth/login` to see the login page. Clicking the button will start the authorization flow.
-   **Start/Stop Sharing:** API endpoints (`/share/start`, `/share/stop`) are available for this feature. You can build a UI to interact with them.
-   **Personal Widget:** Get your own currently playing data from `https://your-project.vercel.app/public/widget.html`.
