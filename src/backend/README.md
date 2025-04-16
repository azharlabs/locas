# Locas API

A Flask-based API for processing location-based queries with smart location extraction.

## Features

- Process natural language queries with embedded location information
- Automatically extract location data from query text:
  - Google Maps URLs 
  - Address mentions
  - Direct latitude/longitude coordinates
- Provides insights on:
  - Land purchase suitability
  - Business viability
  - Nearby amenities
  - Environmental data

## Setup Instructions

### 1. Prerequisites

- Python 3.7 or higher
- pip package manager

### 2. Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd location-assistant-api
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   ```

### 3. Running the API

Start the Flask server:
```
python app.py
```

The server will start on `http://localhost:5000`.

## Using the API

### Web Interface

Open `http://localhost:5000` in your browser to use the web interface.

### API Endpoints

#### POST /api/process-query

Process a location-based query with embedded location information.

**Request Body:**

```json
{
  "query": "Are there any hospitals near Times Square, New York?"
}
```

or

```json
{
  "query": "Can I start a coffee shop here? https://www.google.com/maps?q=40.7128,-74.0060"
}
```

or

```json
{
  "query": "Any parks near 37.7749, -122.4194?"
}
```

**Response:**

```json
{
  "status": "success",
  "result": "Analysis result text..."
}
```

### Location Format Examples

The API can extract location information from your query in these formats:

1. **Named Locations**:
   - "Are there any restaurants near Empire State Building?"
   - "Can I open a business in Downtown Chicago?"

2. **Addresses**:
   - "Is there a park near 123 Main St, San Francisco, CA?"
   - "Hospitals near Times Square, New York"

3. **Coordinates**:
   - "What's nearby 37.7749, -122.4194?"
   - "Can I buy land at 40.7128, -74.0060?"

4. **Google Maps URLs**:
   - "What's at this location? https://www.google.com/maps?q=37.7749,-122.4194"
   - "Can I start a tea stall here? https://www.google.com/maps/place/Central+Park"

## API Reference

### Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| query | string | Required. The user's question or request, containing embedded location information |

### Response Format

| Field | Type | Description |
|-------|------|-------------|
| status | string | "success", "warning", or "error" |
| message | string | Optional. Additional information or error details |
| result | string | The analysis result (when successful) |

## Testing

A test client is included to verify the API functionality:

```
python test_client.py
```

## Project Structure

- `app.py` - Flask API server
- `assistant/` - Location assistant implementation
  - `location_assistant.py` - Main assistant class
  - `location_parser.py` - Parser for extracting locations from queries
  - `analyzers/` - Analysis modules for different query types
  - `utils/` - Helper utilities
- `models/` - Data models
- `services/` - External service integrations
- `static/` - Web interface files
- `test_client.py` - API test script

## License

[MIT License](LICENSE)