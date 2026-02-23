# Mahjong Winner

This project has been updated to use a React + TypeScript frontend and a Flask backend API.

## Prerequisites

- Python 3.10+
- Node.js and npm

## Backend Setup

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   Or use the provided conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate mahjong2
   ```

2. Run the Flask API server:
   ```bash
   python app.py
   ```
   The backend will run on `http://localhost:5000`.

## Frontend Setup

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install the required npm packages:
   ```bash
   npm install
   ```

3. Run the React development server:
   ```bash
   npm run dev
   ```
   The frontend will run on `http://localhost:5173` (or another port specified by Vite).

## Usage

1. Open the frontend URL in your browser.
2. Configure the game settings.
3. Upload an image of your Mahjong hand.
4. Click "Analyze" to see the results.

