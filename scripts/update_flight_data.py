"""
Script to fetch real flight data from Aviation Stack API and generate updated data for load_data.py
With improved error handling, retry logic, and more detailed debug information
"""
import os
import sys
import json
import random
import asyncio
import httpx
import time
from datetime import datetime, timedelta

# Get API key from environment variable, with fallback to a demo key (limited usage)
API_KEY = os.environ.get("AVIATIONSTACK_API_KEY", "c9768ecf38c9013f3d6d7427cff314d8")
API_BASE_URL = "https://api.aviationstack.com/v1"

# Maximum retries for API calls
MAX_RETRIES = 3
# Base delay for exponential backoff (in seconds)
BASE_DELAY = 2

async def fetch_with_retry(url, params, description="API request"):
    """Make an API request with exponential backoff retry logic"""
    retries = 0
    last_exception = None
    
    while retries < MAX_RETRIES:
        try:
            print(f"Making {description} (attempt {retries+1}/{MAX_RETRIES})")
            print(f"URL: {url}")
            print(f"Params: {params}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Inspect the response structure
                    if "data" in data:
                        if isinstance(data["data"], list):
                            print(f"Success! Received {len(data['data'])} items")
                            if data["data"]:
                                print(f"First item sample: {json.dumps(data['data'][0], indent=2)[:200]}...")
                            return data
                        else:
                            print(f"Warning: 'data' is not a list: {type(data['data'])}")
                    
                    # Check for pagination info
                    if "pagination" in data:
                        print(f"Pagination info: {data['pagination']}")
                    
                    # Check for error messages
                    if "error" in data:
                        print(f"API returned error: {data['error']}")
                        
                    return data
                elif response.status_code == 429:
                    print("Rate limit exceeded, waiting longer before retry")
                    retries += 1
                    # Wait longer for rate limit errors
                    await asyncio.sleep(BASE_DELAY * (2 ** retries) * 2)
                    continue
                else:
                    print(f"Error status {response.status_code}: {response.text}")
                    retries += 1
                    
                    if retries < MAX_RETRIES:
                        delay = BASE_DELAY * (2 ** retries)
                        print(f"Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                    else:
                        return {"error": f"Failed after {MAX_RETRIES} attempts. Last status: {response.status_code}"}
                        
        except Exception as e:
            print(f"Exception during {description}: {str(e)}")
            last_exception = e
            retries += 1
            
            if retries < MAX_RETRIES:
                delay = BASE_DELAY * (2 ** retries)
                print(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
    
    return {"error": f"Failed after {MAX_RETRIES} attempts. Last error: {str(last_exception)}"}

async def get_flights():
    """Fetch flight data from Aviation Stack API, focusing on Air France and Transavia"""
    print("\n=== FETCHING FLIGHT DATA ===")
    print(f"API Key: {'VALID' if API_KEY else 'MISSING'} (last 4 chars: {API_KEY[-4:] if API_KEY else 'NONE'})")
    
    # Array to store our API approaches
    approaches = []
    
    # Approach 1: Query for Air France flights
    approaches.append({
        "description": "Air France flights",
        "params": {
            "access_key": API_KEY,
            "airline_iata": "AF", 
            "limit": 100
        }
    })
    
    # Approach 2: Query for Transavia flights
    approaches.append({
        "description": "Transavia flights",
        "params": {
            "access_key": API_KEY,
            "airline_iata": "HV",
            "limit": 100
        }
    })
    
    # Approach 3: Query for active flights (may contain AF or HV)
    approaches.append({
        "description": "Active flights",
        "params": {
            "access_key": API_KEY,
            "flight_status": "active",
            "limit": 100
        }
    })
    
    # Approach 4: Query for flights from CDG (Air France hub)
    approaches.append({
        "description": "Flights from Paris CDG",
        "params": {
            "access_key": API_KEY,
            "dep_iata": "CDG",
            "limit": 100
        }
    })
    
    # Approach 5: Query for flights from AMS (Transavia hub)
    approaches.append({
        "description": "Flights from Amsterdam",
        "params": {
            "access_key": API_KEY,
            "dep_iata": "AMS",
            "limit": 100
        }
    })
    
    # Approach 6: Query with minimal filters (last resort)
    approaches.append({
        "description": "Minimal filters",
        "params": {
            "access_key": API_KEY,
            "limit": 100
        }
    })
    
    # Try each approach in order
    for i, approach in enumerate(approaches):
        print(f"\n> Approach {i+1}: {approach['description']}")
        
        result = await fetch_with_retry(
            f"{API_BASE_URL}/flights", 
            approach["params"], 
            f"Approach {i+1}: {approach['description']}"
        )
        
        if "error" in result:
            print(f"Approach {i+1} failed: {result['error']}")
            continue
        
        # Check if we got any data
        if "data" in result and isinstance(result["data"], list) and result["data"]:
            print(f"Approach {i+1} returned {len(result['data'])} flights")
            
            # If this is an approach without airline filter, filter for AF/HV
            if approach["params"].get("airline_iata") not in ["AF", "HV", "AF,HV"]:
                af_hv_flights = [f for f in result["data"] 
                                if f.get("airline", {}).get("iata") in ["AF", "HV"]]
                
                if af_hv_flights:
                    print(f"Found {len(af_hv_flights)} Air France and Transavia flights")
                    return {"data": af_hv_flights}
                else:
                    print("No Air France or Transavia flights found in results")
            else:
                # We already filtered for AF/HV in the API call
                return result
        else:
            print(f"Approach {i+1}: No valid data returned")
    
    print("\nAll approaches failed to get Air France or Transavia flight data")
    return {"error": "No flight data available from any query approach"}

async def get_airport_info(iata_code):
    """Fetch info for a specific airport by IATA code"""
    params = {
        "access_key": API_KEY,
        "iata_code": iata_code
    }
    
    return await fetch_with_retry(
        f"{API_BASE_URL}/airports", 
        params, 
        f"Airport info for {iata_code}"
    )

def format_flight_data(flight_data):
    """Format flight data into a structure suitable for load_data.py"""
    flights = []
    bookings = []
    
    # Check if there's an error or no data
    if "error" in flight_data or "data" not in flight_data or not flight_data["data"]:
        print("No flight data available or API error. Using sample data instead.")
        # Generate sample data specifically for Air France and Transavia
        return generate_sample_data()
    
    # Process actual flight data
    booking_id = 1
    for flight in flight_data["data"][:12]:  # Take up to 12 flights
        try:
            # Extract flight information
            flight_number = flight.get("flight", {}).get("iata", f"XX{random.randint(1000, 9999)}")
            airline = flight.get("airline", {})
            airline_name = airline.get("name", "Unknown Airline")
            airline_iata = airline.get("iata", "XX")
            
            # Only use Air France (AF) and Transavia (HV) flights
            if airline_iata not in ["AF", "HV"]:
                continue
            
            # Extract departure and arrival information
            departure = flight.get("departure", {})
            arrival = flight.get("arrival", {})
            
            departure_airport = departure.get("iata", "XXX")
            arrival_airport = arrival.get("iata", "YYY")
            
            # Get city names for departure and arrival
            departure_city = get_city_name(departure_airport)
            arrival_city = get_city_name(arrival_airport)
            
            # Create weather data (simulated)
            weather_conditions = ["Sunny", "Cloudy", "Rainy", "Clear", "Foggy", "Windy", "Hot", "Cold"]
            weather = {
                "departure": {
                    "condition": random.choice(weather_conditions),
                    "temperature": f"{random.randint(10, 35)}°C"
                },
                "arrival": {
                    "condition": random.choice(weather_conditions),
                    "temperature": f"{random.randint(10, 35)}°C"
                }
            }
            
            # Create context description based on real airport names if available
            dep_airport_name = departure.get("airport", get_airport_name(departure_airport))
            arr_airport_name = arrival.get("airport", get_airport_name(arrival_airport))
            context = f"International flight from {dep_airport_name} to {arr_airport_name}"
            
            # Extract aircraft information (based on AviationStack API structure)
            aircraft = flight.get("aircraft", {})
            if aircraft and isinstance(aircraft, dict):
                # Use real aircraft data if available
                aircraft_info = {
                    "registration": aircraft.get("registration", f"F-G{random.choice(['X', 'H', 'P'])}{random.choice(['T', 'K', 'L'])}{random.choice(['A', 'B', 'C'])}{random.choice(['R', 'S', 'T'])}"),
                    "iata": aircraft.get("iata", get_aircraft_iata_for_airline(airline_iata)),
                    "icao": aircraft.get("icao", get_aircraft_icao_for_airline(airline_iata)),
                    "icao24": aircraft.get("icao24", generate_icao24())
                }
            else:
                # Generate realistic aircraft data if not available from API
                aircraft_info = {
                    "registration": f"F-G{random.choice(['X', 'H', 'P'])}{random.choice(['T', 'K', 'L'])}{random.choice(['A', 'B', 'C'])}{random.choice(['R', 'S', 'T'])}",
                    "iata": get_aircraft_iata_for_airline(airline_iata),
                    "icao": get_aircraft_icao_for_airline(airline_iata),
                    "icao24": generate_icao24()
                }

            # Create flight entry matching AviationStack API structure
            flight_entry = {
                "id": flight_number,
                "destination": arrival_airport,
                "destination_city": arrival_city,
                "departure": departure_airport,
                "departure_city": departure_city,
                "brand": airline_iata,  # Use actual airline IATA code
                "aircraft": aircraft_info,
                "weather": weather,
                "context": context
            }
            flights.append(flight_entry)
            
            # Create associated booking entries (1-2 per flight)
            num_bookings = random.randint(1, 2)
            for _ in range(num_bookings):
                first_names = ["John", "Jane", "Carlos", "Maria", "Yuki", "Liu", "Fatima", "Olga", "Mohammed", "Anna", "Santiago", "Aisha"]
                last_names = ["Smith", "Doe", "Garcia", "Tanaka", "Wei", "Al-Farsi", "Ivanova", "Khan", "Müller", "Lopez", "Ahmed", "Petrova"]
                
                name = f"{random.choice(first_names)} {random.choice(last_names)}"
                
                currencies = ["USD", "EUR", "GBP", "JPY", "CNY", "AED", "RUB", "INR"]
                status_options = ["gold", "silver", "none"]
                meal_options = ["standard", "vegetarian", "vegan", "halal", "gluten-free"]
                
                delay_options = ["on time", "5 mins", "10 mins", "15 mins", "30 mins", "1 hour"]
                
                booking_entry = {
                    "id": booking_id,
                    "name": name,
                    "flight": flight_number,
                    "brand": airline_iata,
                    "cost": random.randint(400, 800),
                    "currency": random.choice(currencies),
                    "phone": f"+{random.randint(1, 99)}-{random.randint(10, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                    "options": {
                        "luggage": f"{random.randint(15, 30)}kg",
                        "meals": random.choice(meal_options),
                        "delay": random.choice(delay_options)
                    },
                    "skyid": f"SKY{random.randint(10000, 99999)}",
                    "status": random.choice(status_options)
                }
                
                bookings.append(booking_entry)
                booking_id += 1
                
        except Exception as e:
            print(f"Error processing flight: {e}", file=sys.stderr)
            continue
            
    # If we couldn't get enough flights, pad with some fictional ones
    if len(flights) < 12:
        print(f"Only found {len(flights)} real flights, adding {12 - len(flights)} fictional ones")
        
        # Generate fictional flights
        fictional_flights, fictional_bookings = generate_additional_flights(
            12 - len(flights), 
            booking_id, 
            existing_flight_numbers=[f["id"] for f in flights]
        )
        
        flights.extend(fictional_flights)
        bookings.extend(fictional_bookings)
    
    return {
        "flights": flights,
        "bookings": bookings
    }

def generate_additional_flights(count, start_booking_id, existing_flight_numbers=None):
    """Generate additional fictional flights to fill gaps"""
    flights = []
    bookings = []
    booking_id = start_booking_id
    
    existing_flight_numbers = existing_flight_numbers or []
    
    # Create fictional flights focused on Air France and Transavia
    for i in range(count):
        # Alternate between Air France (AF) and Transavia (HV)
        if i % 2 == 0:
            brand = "AF"  # Air France
            flight_number = generate_unique_flight_number("AF", existing_flight_numbers)
        else:
            brand = "HV"  # Transavia
            flight_number = generate_unique_flight_number("HV", existing_flight_numbers)
        
        existing_flight_numbers.append(flight_number)
        
        # Select airports based on airline
        airports = select_airports_for_airline(brand)
        
        weather_conditions = ["Sunny", "Cloudy", "Rainy", "Clear", "Foggy", "Windy", "Hot", "Cold"]
        weather = {
            "departure": {
                "condition": random.choice(weather_conditions),
                "temperature": f"{random.randint(10, 35)}°C"
            },
            "arrival": {
                "condition": random.choice(weather_conditions),
                "temperature": f"{random.randint(10, 35)}°C"
            }
        }
        
        departure = airports["departure"]
        arrival = airports["arrival"]
        
        # Add aircraft information for fictional flights
        aircraft_info = {
            "registration": f"F-G{random.choice(['X', 'H', 'P'])}{random.choice(['T', 'K', 'L'])}{random.choice(['A', 'B', 'C'])}{random.choice(['R', 'S', 'T'])}",
            "iata": get_aircraft_iata_for_airline(brand),
            "icao": get_aircraft_icao_for_airline(brand),
            "icao24": generate_icao24()
        }
        
        flight_entry = {
            "id": flight_number,
            "destination": arrival["code"],
            "destination_city": get_city_name(arrival["code"]),
            "departure": departure["code"],
            "departure_city": get_city_name(departure["code"]),
            "brand": brand,
            "aircraft": aircraft_info,
            "weather": weather,
            "context": f"International flight from {departure['name']} to {arrival['name']}"
        }
        flights.append(flight_entry)
        
        # Create associated bookings
        num_bookings = random.randint(1, 2)
        for _ in range(num_bookings):
            first_names = ["John", "Jane", "Carlos", "Maria", "Yuki", "Liu", "Fatima", "Olga", "Mohammed", "Anna", "Santiago", "Aisha"]
            last_names = ["Smith", "Doe", "Garcia", "Tanaka", "Wei", "Al-Farsi", "Ivanova", "Khan", "Müller", "Lopez", "Ahmed", "Petrova"]
            
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            currencies = ["USD", "EUR", "GBP", "JPY", "CNY", "AED", "RUB", "INR"]
            status_options = ["gold", "silver", "none"]
            meal_options = ["standard", "vegetarian", "vegan", "halal", "gluten-free"]
            delay_options = ["on time", "5 mins", "10 mins", "15 mins", "30 mins", "1 hour"]
            
            booking_entry = {
                "id": booking_id,
                "name": name,
                "flight": flight_number,
                "brand": brand,
                "cost": random.randint(400, 800),
                "currency": random.choice(currencies),
                "phone": f"+{random.randint(1, 99)}-{random.randint(10, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                "options": {
                    "luggage": f"{random.randint(15, 30)}kg",
                    "meals": random.choice(meal_options),
                    "delay": random.choice(delay_options)
                },
                "skyid": f"SKY{random.randint(10000, 99999)}",
                "status": random.choice(status_options)
            }
            
            bookings.append(booking_entry)
            booking_id += 1
    
    return flights, bookings

def generate_unique_flight_number(prefix, existing_numbers):
    """Generate a unique flight number that doesn't exist in the list"""
    while True:
        if prefix == "AF":
            number = f"AF{random.randint(1000, 1999)}"
        else:
            number = f"HV{random.randint(2000, 2999)}"
        
        if number not in existing_numbers:
            return number

def select_airports_for_airline(airline):
    """Select appropriate airports for a given airline"""
    if airline == "AF":  # Air France
        # Air France operates from CDG and ORY as main hubs
        departure_options = [
            {"code": "CDG", "name": "Paris Charles de Gaulle"},
            {"code": "ORY", "name": "Paris Orly"}
        ]
        
        # Air France destinations
        arrival_options = [
            {"code": "JFK", "name": "New York JFK"},
            {"code": "LHR", "name": "London Heathrow"},
            {"code": "FCO", "name": "Rome Fiumicino"},
            {"code": "MAD", "name": "Madrid Barajas"},
            {"code": "AMS", "name": "Amsterdam Schiphol"},
            {"code": "BOS", "name": "Boston Logan"},
            {"code": "ATL", "name": "Atlanta Hartsfield-Jackson"},
            {"code": "LAX", "name": "Los Angeles International"}
        ]
    else:  # Transavia (HV)
        # Transavia operates from AMS and ORY as main hubs
        departure_options = [
            {"code": "AMS", "name": "Amsterdam Schiphol"},
            {"code": "ORY", "name": "Paris Orly"},
            {"code": "EIN", "name": "Eindhoven Airport"}
        ]
        
        # Transavia destinations (focus on leisure destinations)
        arrival_options = [
            {"code": "BCN", "name": "Barcelona El Prat"},
            {"code": "ALC", "name": "Alicante"},
            {"code": "FAO", "name": "Faro"},
            {"code": "LIS", "name": "Lisbon"},
            {"code": "AGP", "name": "Malaga"},
            {"code": "NAP", "name": "Naples"},
            {"code": "ACE", "name": "Lanzarote"},
            {"code": "ATH", "name": "Athens"}
        ]
    
    departure = random.choice(departure_options)
    # Filter out the departure airport from arrival options
    valid_arrivals = [a for a in arrival_options if a["code"] != departure["code"]]
    arrival = random.choice(valid_arrivals)
    
    return {
        "departure": departure,
        "arrival": arrival
    }

def get_aircraft_iata_for_airline(airline_iata):
    """Get appropriate aircraft IATA codes for specific airlines"""
    if airline_iata == "AF":  # Air France
        # Air France commonly uses these aircraft types
        aircraft_types = ["77W", "772", "359", "350", "320", "321", "319", "318"]
    elif airline_iata == "HV":  # Transavia
        # Transavia primarily uses Boeing 737 variants
        aircraft_types = ["737", "73H", "73G", "73W"]
    else:
        # Generic aircraft types
        aircraft_types = ["320", "321", "737", "77W", "350"]
    
    return random.choice(aircraft_types)

def get_aircraft_icao_for_airline(airline_iata):
    """Get appropriate aircraft ICAO codes for specific airlines"""
    if airline_iata == "AF":  # Air France
        # Air France fleet ICAO codes
        aircraft_types = ["B77W", "B772", "A359", "A350", "A320", "A321", "A319", "A318"]
    elif airline_iata == "HV":  # Transavia
        # Transavia fleet ICAO codes
        aircraft_types = ["B737", "B738", "B739", "B37M"]
    else:
        # Generic aircraft ICAO codes
        aircraft_types = ["A320", "A321", "B737", "B77W", "A350"]
    
    return random.choice(aircraft_types)

def generate_icao24():
    """Generate a realistic ICAO24 transponder code (6 hex characters)"""
    # ICAO24 codes are 6 hexadecimal characters
    hex_chars = "0123456789ABCDEF"
    return "".join(random.choice(hex_chars) for _ in range(6))

def get_city_name(iata_code):
    """Convert IATA code to city/capital name"""
    city_dict = {
        # Major international airports
        "JFK": "New York",
        "LHR": "London", 
        "CDG": "Paris",
        "ORY": "Paris",
        "LAX": "Los Angeles",
        "AMS": "Amsterdam",
        "FRA": "Frankfurt",
        "MAD": "Madrid",
        "SIN": "Singapore",
        "HKG": "Hong Kong",
        "SYD": "Sydney",
        "GRU": "São Paulo",
        "DXB": "Dubai",
        "BCN": "Barcelona",
        "FCO": "Rome",
        "ALC": "Alicante",
        "FAO": "Faro",
        "LIS": "Lisbon",
        "AGP": "Malaga",
        "NAP": "Naples",
        "ACE": "Lanzarote",
        "ATH": "Athens",
        "EIN": "Eindhoven",
        "BOS": "Boston",
        "ATL": "Atlanta",
        # Additional airports from real data
        "YXE": "Saskatoon",
        "YVR": "Vancouver",
        "YYZ": "Toronto",
        "KIX": "Osaka",
        "HND": "Tokyo",
        "CLJ": "Cluj-Napoca",
        "OTP": "Bucharest",
        "SBN": "South Bend",
        "MSP": "Minneapolis",
        "BRI": "Bari",
        "LIN": "Milan",
        "PVG": "Shanghai",
        "BOO": "Bodø",
        "OSL": "Oslo",
        "SSH": "Sharm el-Sheikh",
        "DOH": "Doha",
        "RUH": "Riyadh",
        "DWD": "Dawadmi",
        "RSI": "Dawadmi Region",
        "NUM": "Neom",
        "SXM": "Sint Maarten",
        "SAB": "Saba",
        "FUK": "Fukuoka",
        "OKJ": "Okayama", 
        "KOJ": "Kagoshima",
        "NGS": "Nagasaki",
        "KMJ": "Kumamoto",
        "JNB": "Johannesburg",
        "BUQ": "Bulawayo",
        # US airports
        "DFW": "Dallas",
        "DEN": "Denver",
        "ORD": "Chicago",
        "MIA": "Miami",
        "SEA": "Seattle",
        # African airports
        "NLA": "Ndola",
        "FBM": "Lubumbashi",
        "NBO": "Nairobi",
        "HDS": "Hoedspruit",
        "LUN": "Lusaka",
        "CAI": "Cairo",
        "LOS": "Lagos",
        "CPT": "Cape Town",
        # European airports  
        "MUC": "Munich",
        "VIE": "Vienna",
        "ZUR": "Zurich",
        "ARN": "Stockholm",
        "CPH": "Copenhagen",
        "HEL": "Helsinki",
        # Asian airports
        "ICN": "Seoul",
        "NRT": "Tokyo",
        "BKK": "Bangkok",
        "KUL": "Kuala Lumpur",
        "CGK": "Jakarta",
        "MNL": "Manila"
    }
    return city_dict.get(iata_code, f"Ville {iata_code}")

def get_airport_name(iata_code):
    """Convert IATA code to airport name"""
    airport_dict = {
        "JFK": "New York JFK",
        "LHR": "London Heathrow",
        "CDG": "Paris Charles de Gaulle",
        "ORY": "Paris Orly",
        "LAX": "Los Angeles",
        "AMS": "Amsterdam Schiphol",
        "FRA": "Frankfurt",
        "MAD": "Madrid Barajas",
        "SIN": "Singapore Changi",
        "HKG": "Hong Kong",
        "SYD": "Sydney",
        "GRU": "São Paulo",
        "DXB": "Dubai",
        "BCN": "Barcelona",
        "FCO": "Rome Fiumicino",
        "ALC": "Alicante",
        "FAO": "Faro",
        "LIS": "Lisbon",
        "AGP": "Malaga",
        "NAP": "Naples",
        "ACE": "Lanzarote",
        "ATH": "Athens",
        "EIN": "Eindhoven",
        "BOS": "Boston Logan",
        "ATL": "Atlanta Hartsfield-Jackson"
    }
    return airport_dict.get(iata_code, f"Airport {iata_code}")

def generate_sample_data():
    """Generate sample data if API call fails"""
    print("Generating sample data for Air France and Transavia airlines")
    flights = []
    bookings = []
    flight_numbers = []
    
    # Create 12 fictional flights
    for i in range(12):
        # Alternate between Air France (AF) and Transavia (HV)
        if i % 2 == 0:
            brand = "AF"  # Air France
            flight_number = generate_unique_flight_number("AF", flight_numbers)
        else:
            brand = "HV"  # Transavia
            flight_number = generate_unique_flight_number("HV", flight_numbers)
            
        flight_numbers.append(flight_number)
        
        # Select appropriate airports based on airline
        airports = select_airports_for_airline(brand)
        departure = airports["departure"]
        arrival = airports["arrival"]
        
        # Add aircraft information for sample data
        aircraft_info = {
            "registration": f"F-G{random.choice(['X', 'H', 'P'])}{random.choice(['T', 'K', 'L'])}{random.choice(['A', 'B', 'C'])}{random.choice(['R', 'S', 'T'])}",
            "iata": get_aircraft_iata_for_airline(brand),
            "icao": get_aircraft_icao_for_airline(brand),
            "icao24": generate_icao24()
        }
        
        # Create weather data
        weather_conditions = ["Sunny", "Cloudy", "Rainy", "Clear", "Foggy", "Windy", "Hot", "Cold"]
        weather = {
            "departure": {
                "condition": random.choice(weather_conditions),
                "temperature": f"{random.randint(10, 35)}°C"
            },
            "arrival": {
                "condition": random.choice(weather_conditions),
                "temperature": f"{random.randint(10, 35)}°C"
            }
        }
        
        flight_entry = {
            "id": flight_number,
            "destination": arrival["code"],
            "destination_city": get_city_name(arrival["code"]),
            "departure": departure["code"],
            "departure_city": get_city_name(departure["code"]),
            "brand": brand,
            "aircraft": aircraft_info,
            "weather": weather,
            "context": f"International flight from {departure['name']} to {arrival['name']}"
        }
        flights.append(flight_entry)
        
        # Create bookings for this flight (1-2 per flight)
        num_bookings = random.randint(1, 2)
        for j in range(num_bookings):
            booking_id = len(bookings) + 1
            
            first_names = ["John", "Jane", "Carlos", "Maria", "Yuki", "Liu", "Fatima", "Olga", "Mohammed", "Anna", "Santiago", "Aisha"]
            last_names = ["Smith", "Doe", "Garcia", "Tanaka", "Wei", "Al-Farsi", "Ivanova", "Khan", "Müller", "Lopez", "Ahmed", "Petrova"]
            
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            currencies = ["USD", "EUR", "GBP", "JPY", "CNY", "AED", "RUB", "INR"]
            status_options = ["gold", "silver", "none"]
            meal_options = ["standard", "vegetarian", "vegan", "halal", "gluten-free"]
            delay_options = ["on time", "5 mins", "10 mins", "15 mins", "30 mins", "1 hour"]
            
            booking_entry = {
                "id": booking_id,
                "name": name,
                "flight": flight_number,
                "brand": brand,
                "cost": random.randint(400, 800),
                "currency": random.choice(currencies),
                "phone": f"+{random.randint(1, 99)}-{random.randint(10, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                "options": {
                    "luggage": f"{random.randint(15, 30)}kg",
                    "meals": random.choice(meal_options),
                    "delay": random.choice(delay_options)
                },
                "skyid": f"SKY{random.randint(10000, 99999)}",
                "status": random.choice(status_options)
            }
            
            bookings.append(booking_entry)
    
    return {
        "flights": flights,
        "bookings": bookings
    }

def generate_python_code(data):
    """Generate Python code for updating load_data.py"""
    flights = data["flights"]
    bookings = data["bookings"]
    
    # Format flights as Python code
    flights_code = "def get_flights_data():\n    return [\n"
    for flight in flights:
        flight_str = "        " + json.dumps(flight, ensure_ascii=False)
        flight_str = flight_str.replace('"', "'").replace(": '", ": \"").replace("',", "\",").replace("'}", "\"}")
        flights_code += flight_str + ",\n"
    flights_code = flights_code[:-2] + "\n    ]\n"
    
    # Format bookings as Python code
    bookings_code = "def get_bookings_data():\n    return [\n"
    for booking in bookings:
        booking_str = "    " + json.dumps(booking, ensure_ascii=False)
        booking_str = booking_str.replace('"', "'").replace(": '", ": \"").replace("',", "\",").replace("'}", "\"}")
        bookings_code += booking_str + ",\n"
    bookings_code = bookings_code[:-2] + "\n    ]\n"
    
    # Combine into final code with generation timestamp
    final_code = f"""# Flight and booking data generated from AviationStack API
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Contains a mix of real and fictional flight data

{bookings_code}

{flights_code}
"""
    
    return final_code

async def main():
    """Main entry point"""
    print("Fetching flight data from Aviation Stack API...")
    
    # Fetch real flight data
    flight_data = await get_flights()
    
    # Check for API errors
    if "error" in flight_data:
        print(f"ERROR: API request failed: {flight_data['error']}")
    elif "data" not in flight_data or not flight_data["data"]:
        print("WARNING: API returned empty data array. This may be due to:")
        print("  - Invalid or expired API key")
        print("  - No flights matching the query parameters")
        print("  - API service limitations")
        print("\nFalling back to sample data...")
    
    # Format data for use in load_data.py
    formatted_data = format_flight_data(flight_data)
    
    # Generate Python code
    python_code = generate_python_code(formatted_data)
    
    # Get script directory and project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Output path
    output_path = os.path.join(project_root, "app", "api", "data", "load_data.py")
    backup_path = os.path.join(project_root, "app", "api", "data", "load_data.py.bak")
    
    # Create backup of original file
    if os.path.exists(output_path):
        print(f"Creating backup of original file as {backup_path}")
        with open(output_path, 'r', encoding='utf-8') as original:
            with open(backup_path, 'w', encoding='utf-8') as backup:
                backup.write(original.read())
    
    # Write new data
    print(f"Writing updated flight and booking data to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(python_code)
    
    print("Data update complete!")
    print(f"Generated {len(formatted_data['flights'])} flights and {len(formatted_data['bookings'])} bookings")
    
    # Also save raw data for reference
    json_path = os.path.join(project_root, "data", "latest_flight_data.json")
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(flight_data, f, indent=2)
    print(f"Raw API response saved to {json_path}")

if __name__ == "__main__":
    asyncio.run(main())