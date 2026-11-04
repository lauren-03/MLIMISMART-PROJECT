---
title: MlimiSmart
colorFrom: green
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# MlimiSmart

Tea farming advisory system for smallholder farmers in Thyolo and Mulanje.
Farmers use it through the website, SMS or USSD, in English or Chichewa.

## Stack

- Frontend: React, Bootstrap (`frontend/`)
- Backend: FastAPI, MySQL (`backend/`)
- Machine learning: scikit-learn
- Weather: Open-Meteo (forecast and daily history)
- Climate datasets: ERA5-Land soil moisture, NASA POWER, CHIRPS monthly rainfall
- Wording of advice and leaf photos: Google Gemini
- SMS and USSD: Africa's Talking

## Models

| Model | What it does | Trained on |
|---|---|---|
| Topic classifier | Works out what a question is about | Farmer questions |
| Rain model | Predicts rain (1 mm or more) for tomorrow in each area | Daily weather, ERA5-Land soil moisture, NASA POWER and CHIRPS since 2016, 23 areas |
| Advice model | Chooses the best action for the topic and situation | Past weather and soil moisture days labelled with tea guidance, plus farmer ratings |

The weather history and climate datasets are updated every day, and the rain and advice models are retrained.
Each rain prediction is checked against the rain that actually fell.
Farmers rate each piece of advice, and the advice model retrains after every 5 new ratings.
Results and training history are shown under Admin > AI models.

## Running

1. Start MySQL, then set up the backend:

   ```
   cd backend
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   .venv\Scripts\pip install -r requirements-english-voice.txt   (optional English voice)
   copy .env.example .env
   .venv\Scripts\python create_database.py
   .venv\Scripts\python seed.py
   ```

2. Start the API. The first start downloads the weather history and climate datasets and trains the models, which takes a while.

   ```
   .venv\Scripts\python -m uvicorn app.main:app --port 8000
   ```

3. Start the website:

   ```
   cd frontend
   npm install
   npm run dev
   ```

Open http://localhost:5173. The demo accounts are created by `seed.py`.
