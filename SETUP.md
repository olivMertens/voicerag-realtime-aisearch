# Setting Up Real-Time Flight Information Feature

This document provides instructions for setting up and using the real-time flight information feature in the VoiceRAG application.

## Features Added

The application now includes the following additional capabilities:
- Real-time flight status for any airline around the world
- Airline information lookup
- Airport information lookup
- Dynamic flight data refresh using real aviation data

## Setup Instructions

### 1. Get an Aviation Stack API Key

1. Visit [Aviation Stack](https://aviationstack.com/) and sign up for an API key
2. The free tier provides 500 requests per month, which is sufficient for testing

### 2. Configure the API Key

#### Using AZD

```bash
# Set your Aviation Stack API key
azd env set AVIATIONSTACK_API_KEY your_api_key_here

# If you've already deployed the application, redeploy
azd up
```

#### Manual Configuration

If you're not using AZD, add the following to your `.env` file in the `app/backend` directory:

```
AVIATIONSTACK_API_KEY=your_api_key_here
```

## Using the Real-Time Flight Information

The voice assistant can now answer questions about flights, airlines, and airports using real-time data. For example:

- "What's the status of flight BA123?"
- "Tell me about United Airlines flight UA456"
- "Give me information about Heathrow Airport"
- "Are there any active flights from Lufthansa?"

## API Endpoints

The following endpoints have been added to the API:

- `GET /api/realtime/flights` - Get real-time flight information
  - Query parameters:
    - `flight_iata` - IATA flight code (e.g., BA123)
    - `airline_iata` - IATA airline code (e.g., BA for British Airways)
    - `flight_status` - Flight status (active, scheduled, landed, cancelled, etc.)

- `GET /api/realtime/airlines` - Get airline information

- `GET /api/realtime/airports` - Get airport information
  - Query parameters:
    - `airport_code` - IATA airport code (e.g., LHR for London Heathrow)

## Technical Details

The implementation uses:
- Aviation Stack API for real-time flight data
- FastAPI endpoints in the `app/api/main.py` file
- Tool functions in `app/backend/ragtools.py` to connect to the GPT Realtime API
- System prompt modification in `app/backend/app.py` to instruct the model to use the new tools

## Refreshing Flight Data

The application includes scripts to refresh the flight data with real-world information:

### PowerShell (Windows):
```powershell
.\scripts\update_flight_data.ps1
```

### Bash (Linux/Mac):
```bash
./scripts/update_flight_data.sh
```

These scripts fetch current flight information from the Aviation Stack API and update the `app/api/data/load_data.py` file with a mix of real and fictional flight data. The script will:

1. Create a backup of the original data file
2. Fetch real-time flight data from the API
3. Generate new flight and booking data based on the API response
4. Write the updated data to the `load_data.py` file
5. Save the raw API response as JSON for reference

## Fallback Behavior

If the Aviation Stack API key is not provided or is invalid, the system will:
1. Log a warning message
2. Return an error message in the API response
3. The assistant will inform the user that real-time flight information is currently unavailable

## Data Limitations

Please note that the Aviation Stack API may have limitations in terms of:
- Historical data availability
- Coverage for certain airlines or regions
- Update frequency

The free tier also has request limitations that should be considered for production use.