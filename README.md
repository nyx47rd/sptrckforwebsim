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

---

## 💻 Usage

-   **Personal Widget:** To see your widget, go to `https://your-netlify-app-name.netlify.app/widget.html`. You can embed this URL in your personal website or profile using an `<iframe>`.