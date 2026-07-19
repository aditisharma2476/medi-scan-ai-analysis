# 🩺 MediSkin AI — AI-Powered Skin Disease Detection PWA

> **Analyze skin conditions instantly using AI.** Upload or capture a photo of a skin lesion, rash, or mole and get a structured medical analysis including disease name, confidence score, symptoms, causes, treatments, severity, and contagiousness — all powered by **Groq's Vision LLM**.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Setup & Installation](#-setup--installation)
  - [1. Backend Setup](#1-backend-setup)
  - [2. Frontend Setup](#2-frontend-setup)
- [How to Use](#-how-to-use)
- [API Reference](#-api-reference)
- [PWA Features](#-pwa-features)
- [Deployment Guide](#-deployment-guide)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## ✨ Features

| Feature                   | Description                                                                                                                                   |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **AI Vision Analysis**    | Uses Groq's `llama-3.2-90b-vision-preview` model for dermatological assessment                                                                |
| **Structured Results**    | Disease name, 4 metrics (Probability, Confidence, Accuracy, Risk Level), description, symptoms, causes, treatments, severity, contagious flag |
| **Mobile Camera Capture** | Take a photo directly using your device's rear camera                                                                                         |
| **Drag & Drop Upload**    | Drag images or click to browse — supports JPG, PNG, WEBP                                                                                      |
| **Image Preview**         | See your image before submitting for analysis                                                                                                 |
| **4 Metric Cards**        | Probability, Confidence, Accuracy, and Risk Level shown with colored progress bars and icons                                                  |
| **Doctor Consult Alert**  | Red alert banner when the AI recommends seeing a dermatologist                                                                                |
| **PWA Ready**             | Installable on Android/iOS/Desktop, works offline with cached assets                                                                          |
| **Dark Theme UI**         | Professional medical-grade dark interface optimized for mobile                                                                                |
| **Offline Support**       | Service worker caches static assets; graceful offline error handling                                                                          |

---

## 🛠 Tech Stack

| Layer        | Technology                                                         |
| ------------ | ------------------------------------------------------------------ |
| **Backend**  | Python 3.11+, Flask, Flask-CORS                                    |
| **AI Model** | Groq API — `meta-llama/llama-4-scout-17b-16e-instruct - on_demand` |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (ES6+)                             |
| **PWA**      | Web App Manifest, Service Worker (Cache-First + Network-First)     |
| **Icons**    | Pillow-generated PNG icons at 8 sizes                              |
| **Styling**  | CSS Custom Properties, Flexbox, Grid, Animations                   |

---

## 📂 Project Structure

```
aditi_project/
│
├── backend/                          # Flask API server
│   ├── app.py                        # Main application (routes, Groq integration)
│   ├── requirements.txt              # Python dependencies
│   ├── .env                          # Environment variables (API key)
│   └── .env.example                  # Template for .env
│
├── frontend/                         # PWA frontend
│   ├── index.html                    # Main HTML shell
│   ├── manifest.json                 # PWA manifest (8 icon sizes)
│   ├── sw.js                         # Service worker (caching strategies)
│   ├── css/
│   │   └── style.css                 # Dark theme, responsive styles
│   ├── js/
│   │   └── app.js                    # Upload, camera, API calls, results UI
│   └── icons/                        # Generated PNG icons
│       ├── icon-72.png
│       ├── icon-96.png
│       ├── icon-128.png
│       ├── icon-144.png
│       ├── icon-152.png
│       ├── icon-192.png
│       ├── icon-384.png
│       └── icon-512.png
│
├── generate_icons.py                 # Script to regenerate PWA icons
└── README.md                         # This file
```

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** — [Download Python](https://www.python.org/downloads/)
- **pip** — Comes with Python (verify with `pip --version`)
- **A Groq API Key** — [Get one free at console.groq.com](https://console.groq.com)
- **A modern browser** — Chrome, Edge, or Firefox (for PWA features)

---

## 🔧 Setup & Installation

### 1. Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create your .env file from the template
copy .env.example .env
# (On macOS/Linux: cp .env.example .env)

# Edit .env and add your Groq API key
# Open .env in any text editor and replace:
#   GROQ_API_KEY=gsk_your_api_key_here
# with your actual key from https://console.groq.com

# Start the Flask development server
py app.py
```

The backend will start at **http://localhost:5000**.

**Verify it's running:**

```bash
curl http://localhost:5000/health
# Expected: {"status":"ok","message":"Skin Disease Detection API is running"}
```

### 2. Frontend Setup

You have two options to serve the frontend:

#### Option A: Python HTTP Server (Recommended for testing)

```bash
# Open a new terminal
cd frontend

# Start a simple HTTP server
py -m http.server 8000
```

Then open **http://localhost:8000** in your browser.

#### Option B: VS Code Live Server

1. Open the `frontend/` folder in VS Code
2. Install the "Live Server" extension
3. Right-click `index.html` → "Open with Live Server"

#### Option C: Any Static Server

```bash
# Using Node.js http-server (if you have Node installed)
npx http-server frontend/ -p 8000
```

---

## 🎯 How to Use

### Step 1: Open the App

Navigate to **http://localhost:8000** (or wherever you're serving the frontend).

### Step 2: Upload or Capture an Image

**Upload method:**

- Click the upload zone (or drag & drop an image)
- Select a JPG, PNG, or WEBP file (max 10 MB)

**Camera method:**

- Click "Capture with Camera"
- Allow camera permissions when prompted
- Point your camera at the skin condition
- Click "Capture" to take a photo

### Step 3: Preview & Analyze

- Review the image preview
- Click **"Analyze Skin Condition"**
- Wait a few seconds while the AI processes the image

### Step 4: Review Results

The results dashboard shows:

| Field                  | Description                                            |
| ---------------------- | ------------------------------------------------------ |
| **Uploaded Image**     | Thumbnail of the analyzed image shown at the top       |
| **Detected Condition** | The most likely skin disease name                      |
| **Probability**        | Likelihood this specific condition is present (0–100%) |
| **Confidence**         | AI confidence in the overall analysis (0–100%)         |
| **Accuracy**           | Derived score averaging probability and confidence     |
| **Risk Level**         | Inverse of accuracy — higher means more caution needed |
| **Severity**           | Mild / Moderate / Severe / Unknown                     |
| **Contagious**         | Yes / No / Unknown                                     |
| **Description**        | Brief explanation of the condition                     |
| **Symptoms**           | 3-5 common symptoms                                    |
| **Causes**             | 2-4 possible causes or risk factors                    |
| **Treatments**         | 2-4 recommended treatments                             |
| **⚠️ Consult Doctor**  | Red alert if professional consultation is advised      |

### Step 5: New Analysis

Click **"New Analysis"** to upload another image.

---

## 🌐 API Reference

### Health Check

```
GET /health
```

**Response:**

```json
{
  "status": "ok",
  "message": "Skin Disease Detection API is running"
}
```

### Analyze Skin Image

```
POST /analyze
Content-Type: multipart/form-data

Body:
  image: <file>  (JPG, PNG, or WEBP, max 10 MB)
```

**Success Response (200):**

```json
{
  "disease_name": "Actinic Keratosis",
  "probability": 85,
  "confidence": 87,
  "description": "A rough, scaly patch on the skin caused by years of sun exposure...",
  "symptoms": [
    "Rough, dry, scaly patches",
    "Flat or slightly raised lesions",
    "Pink, red, or brown discoloration"
  ],
  "causes": ["Chronic sun exposure", "Fair skin", "Weakened immune system"],
  "treatments": [
    "Cryotherapy (freezing)",
    "Topical medications",
    "Photodynamic therapy"
  ],
  "severity": "Mild",
  "contagious": false,
  "consult_doctor": true
}
```

**Error Response (400/500):**

```json
{
  "error": "No image file provided. Use field name 'image'."
}
```

---

## 📱 PWA Features

### Install on Device

**Android (Chrome):**

1. Open the app in Chrome
2. Tap the "Install" banner at the bottom (or the browser menu → "Install app")
3. The app will launch in standalone mode with no browser chrome

**iOS (Safari):**

1. Open the app in Safari
2. Tap the Share button
3. Scroll down and tap "Add to Home Screen"
4. The app will appear as a standalone icon on your home screen

**Desktop (Chrome/Edge):**

1. Click the install icon in the address bar
2. Or use the install banner at the bottom of the page

### Offline Behavior

- **Static assets** (HTML, CSS, JS, icons) are cached on first load and work offline
- **API calls** show a friendly error message when offline
- The service worker automatically updates the cache when new versions are available

---

## 🚀 Deployment Guide

### Deploy Backend to Production

#### Option A: Render

1. Push the `backend/` folder to a GitHub repo
2. On [Render.com](https://render.com), create a new "Web Service"
3. Connect your repo
4. Settings:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment Variable:** Add `GROQ_API_KEY`

#### Option B: Railway

1. Push to GitHub
2. On [Railway.app](https://railway.app), deploy from GitHub
3. Add `GROQ_API_KEY` as an environment variable
4. Railway auto-detects Python and runs `gunicorn app:app`

#### Option C: VPS (DigitalOcean, Linode, etc.)

```bash
# SSH into your server
git clone <your-repo>
cd aditi_project/backend

# Install dependencies
pip install -r requirements.txt

# Set up environment
export GROQ_API_KEY=gsk_your_key_here

# Run with gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Or use a process manager
# Install: pip install supervisor
# Then configure supervisor to keep the app running
```

### Deploy Frontend

#### Option A: Vercel (Recommended)

1. Push the entire project to GitHub
2. On [Vercel.com](https://vercel.com), import your repo
3. Set:
   - **Root Directory:** `frontend`
   - **Build Command:** (leave empty — it's static)
   - **Output Directory:** `.`
4. Update `js/app.js` to point to your deployed backend URL:
   ```javascript
   const API_BASE = "https://your-backend.onrender.com";
   ```

#### Option B: Netlify

1. Drag & drop the `frontend/` folder onto [Netlify Drop](https://app.netlify.com/drop)
2. Or connect your GitHub repo
3. Update the API URL in `js/app.js` to your production backend

#### Option C: GitHub Pages

```bash
# Push the frontend folder to a gh-pages branch
cd frontend
git init
git checkout -b gh-pages
git add .
git commit -m "Deploy frontend"
git remote add origin https://github.com/your-username/your-repo.git
git push origin gh-pages
```

Then enable GitHub Pages in your repo settings, pointing to the `gh-pages` branch.

---

## ❗ Troubleshooting

### Backend Issues

| Problem                | Solution                                                            |
| ---------------------- | ------------------------------------------------------------------- |
| `GROQ_API_KEY not set` | Create a `.env` file in `backend/` with `GROQ_API_KEY=gsk_your_key` |
| `ModuleNotFoundError`  | Run `pip install -r requirements.txt`                               |
| Port 5000 in use       | Change port: `python app.py` — or set `PORT=5001` in `.env`         |
| CORS errors            | Ensure Flask-CORS is installed. The app has `CORS(app)` enabled     |

### Frontend Issues

| Problem                        | Solution                                                                                |
| ------------------------------ | --------------------------------------------------------------------------------------- |
| "Failed to fetch" error        | Ensure the backend is running on port 5000                                              |
| Camera not working             | Use HTTPS or localhost. Camera requires a secure context                                |
| PWA not installing             | Use HTTPS or localhost. PWA requires a secure context                                   |
| Icons not showing              | Run `python generate_icons.py` to regenerate PNG icons                                  |
| Service worker not registering | Check browser console for errors. Ensure `sw.js` is in the root of the served directory |

### Groq API Issues

| Problem             | Solution                                                                          |
| ------------------- | --------------------------------------------------------------------------------- |
| Rate limited        | Groq has rate limits on free tier. Wait and retry                                 |
| Invalid API key     | Verify your key at https://console.groq.com                                       |
| Model not available | The app uses `llama-3.2-90b-vision-preview`. Check Groq docs for available models |

---

## 📄 License

This project is for **educational and informational purposes only**. It is **not a medical device** and should **not** be used as a substitute for professional medical advice, diagnosis, or treatment.

---

## 🙏 Acknowledgments

- **Groq** for providing the fast Vision LLM API
- **Flask** for the lightweight Python web framework
- **Pillow** for image processing capabilities

---

_Built with ❤️ for better skin health awareness._
