# Last.fm Now Playing Widget

This project provides a personal "Now Playing" widget that displays the track you are currently listening to, using the Last.fm API. It is built with FastAPI and designed for easy deployment on Netlify.

## ✨ Features

-   **Personal "Now Playing" Widget:** An embeddable widget that shows your currently playing song from Last.fm.
-   **Real-time Updates:** The widget polls the Last.fm API periodically to show your latest track.
-   **Easy Deployment:** Designed for quick and easy deployment on Netlify.
-   **Lightweight:** A simple and efficient backend powered by FastAPI.

## 🛠️ Tech Stack

-   **Backend:** [FastAPI](https://fastapi.tiangolo.com/)
-   **Deployment:** [Netlify](https://www.netlify.com/)
-   **Music Service:** [Last.fm Web API](https://www.last.fm/api)

---

## 🚀 Setup and Deployment Guide

Follow these steps to deploy this project on your own Netlify account.

### Step 1: Fork the Project

1.  **Fork** this GitHub repository to your own account.

### Step 2: Get a Last.fm API Key

1.  Go to the [Last.fm API page](https://www.last.fm/api/account/create) and create an API account.
2.  Fill out the form. You don't need a callback URL or application homepage, so you can enter any valid URL (e.g., your GitHub profile).
3.  Once created, you will see your **API Key**. Keep this key safe.

### Step 3: Deploy to Netlify

1.  Log in to your [Netlify](https://www.netlify.com/) account.
2.  Click **"Add new site" -> "Import an existing project"** and select the repository you forked on GitHub.
3.  Netlify will automatically detect the settings from the `netlify.toml` file.

### Step 4: Configure Environment Variables

Before deploying, Netlify will prompt you to add environment variables. You can also add them later in your Netlify project's settings (**Site settings > Build & deploy > Environment**).

Create the following environment variables:

| Variable Name     | Description                                | Example Value              |
| ----------------- | ------------------------------------------ | -------------------------- |
| `LASTFM_API_KEY`  | The API Key from your Last.fm API account. | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `LASTFM_USERNAME` | Your Last.fm username.                     | `your_lastfm_username`     |

After setting these variables, click **"Deploy site"**. Once the deployment is complete, your widget will be live.

To get the personal "Now Playing" widget (`/api/now-playing`) working, you need to obtain a `refresh_token` for your own Spotify account. This script simplifies the process.

1.  **Add a new Redirect URI to your Spotify App:**
    -   Go to your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) and select your app.
    -   Click "Edit Settings".
    -   Add `https://example.com/callback` to your list of Redirect URIs and save.

2.  **Prepare your local environment:**
    -   Make sure you have cloned the project and installed dependencies (`pip install -r requirements.txt`).
    -   Create a `.env` file in the project's root directory.
    -   Fill in `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` from your dashboard.
    -   Set `SPOTIFY_REDIRECT_URI` to `https://example.com/callback`.

3.  **Run the script:**
    -   Run the following command in your terminal:
        ```bash
        python generate_token.py
        ```
    -   The script will give you a URL. Open it, log in, and grant permissions.
    -   You will be redirected to an `example.com` page that doesn't exist. This is expected. Copy the full URL from your browser's address bar.
    -   Paste the URL back into your terminal when prompted.

4.  **Set the Environment Variable:**
    -   The script will print your `Refresh Token`. Copy this value.
    -   Go to your Vercel project settings and set the `MY_SPOTIFY_REFRESH_TOKEN` environment variable to the value you just copied.

### Step 6: Deploy the Project

Vercel will automatically deploy any changes to your repository's `main` branch. After setting the environment variables, you can trigger a new deployment from the Vercel dashboard
---

## 💻 Usage

-   **Personal Widget:** To see your widget, go to `https://your-netlify-app-name.netlify.app/widget.html`. You can embed this URL in your personal website or profile using an `<iframe>`.
