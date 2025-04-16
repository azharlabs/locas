# Locas - Location Context Assistant

## Overview

Locas is a location-based context assistant that provides information and insights about geographic locations. The application maintains session context to ensure continuity in the conversation flow, allowing users to refer to previously mentioned locations.

## Features

- Process natural language queries with embedded location information
- Extract location data from query text (Google Maps URLs, addresses, coordinates)
- Provide insights on land purchase suitability, business viability, and more
- Modern React/Next.js frontend with a beautiful chat interface
- Google Authentication for secure access
- Dockerized setup for easy deployment

## Project Structure

```
locas/src/
├── backend/             # Flask backend API
│   ├── assistant/       # Location assistant implementation
│   ├── models/          # Data models
│   ├── services/        # External service integrations
│   ├── app.py           # Flask API server
│   └── ...
├── frontend/            # Next.js frontend
│   ├── components/      # React components
│   ├── lib/             # Utility functions and API client
│   ├── pages/           # Next.js pages and API routes
│   ├── public/          # Static assets
│   └── styles/          # Global styles
└── docker-compose.yml   # Docker setup for both services
```

## Setup Instructions

### Prerequisites

- Node.js 18+
- Python 3.9+
- Docker and Docker Compose
- Google Cloud Platform account (for OAuth)
- OpenAI API key
- Google Maps API key

### Environment Setup

1. Copy the example environment file:
   ```
   cp .env.example .env
   ```

2. Edit the `.env` file and fill in your API keys and secrets:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `GOOGLE_MAPS_API_KEY`: Your Google Maps API key
   - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`: OAuth credentials from Google Cloud Console
   - `NEXTAUTH_SECRET`: A random string (32+ chars) for session encryption

### Running with Docker

1. Start the application using Docker Compose:
   ```
   docker-compose up --build
   ```

2. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

### Development Setup

#### Backend

1. Change to the backend directory:
   ```
   cd backend
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Start the Flask server:
   ```
   python app.py
   ```

#### Frontend

1. Change to the frontend directory:
   ```
   cd frontend
   ```

2. Install JavaScript dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```

## Usage

1. Open the application in your browser: http://localhost:3000
2. Sign in with your Google account
3. Enter location-based queries in the chat interface, such as:
   - "Can I buy land at 40.7128, -74.0060?"
   - "Is there a park near Times Square, New York?"
   - "Can I start a coffee shop here? https://www.google.com/maps?q=37.7749,-122.4194"

## License

[MIT License](LICENSE)