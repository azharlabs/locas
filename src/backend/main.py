import os
import asyncio
from dotenv import load_dotenv

from assistant import LocationAssistant
from models import AppConfig

async def main():
    """Entry point for the application."""
    # Load environment variables
    load_dotenv()
    
    # Get API keys from environment
    config = AppConfig.from_env()
    print("config============", config)
    
    # Check for required API keys
    if not config.openai_api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please create a .env file based on .env.example and add your API keys.")
        return
    
    # Create the location assistant
    assistant = LocationAssistant(
        openai_api_key=config.openai_api_key,
        maps_api_key=config.maps_api_key
    )
    
    # Example queries
    example_queries = [
        "Can I buy land here?",
        "Can I start a tea stall here?",
        "Can I open a restaurant here?",
        "What are the nearest hospitals?",
        "Is there a park nearby?"
    ]
    
    print("\n======== Locas ========")
    print("Example queries:")
    for i, query in enumerate(example_queries, 1):
        print(f"{i}. {query}")
    
    # Get user input
    user_query = input("\nEnter your query (or choose a number from the examples): ")
    
    # Check if user selected an example query
    if user_query.isdigit() and 1 <= int(user_query) <= len(example_queries):
        user_query = example_queries[int(user_query) - 1]
        print(f"Selected query: {user_query}")
    
    print("\nYou can now enter your query with a location in various formats:")
    print("- Include a Google Maps URL")
    print("- Include an address like '123 Main St, San Francisco, CA'")
    print("- Include coordinates like '37.7749, -122.4194'")
    print("- Or you can specify coordinates separately")
    
    # Get the complete query with location (if provided)
    query_with_location = input("\nEnter your query with location or address (or press Enter to use the previous query): ").strip()
    
    if query_with_location:
        # Use the new query with location
        full_query = query_with_location
    else:
        # Use the original query and ask for coordinates
        full_query = user_query
        
        try:
            latitude_input = input("Enter latitude (or press Enter for San Francisco): ").strip()
            longitude_input = input("Enter longitude (or press Enter for San Francisco): ").strip()
            
            # Convert to float if provided, otherwise use None to trigger automatic extraction or defaults
            latitude = float(latitude_input) if latitude_input else None
            longitude = float(longitude_input) if longitude_input else None
            
            print(f"\nProcessing query: {full_query}")
            if latitude is not None and longitude is not None:
                print(f"Using coordinates: Latitude {latitude}, Longitude {longitude}")
            else:
                print("Will try to extract location from query")
            
            print("Processing, please wait...\n")
            
            # Process the query with explicit coordinates
            result = await assistant.process_query(full_query, latitude, longitude)
        except ValueError:
            print("Invalid coordinates format. Will try to extract location from query")
            print("Processing, please wait...\n")
            
            # Process the query without explicit coordinates
            result = await assistant.process_query(full_query)
    
    try:
        # Process the query with location information extracted from the query itself
        if 'result' not in locals():
            print(f"\nProcessing query: {full_query}")
            print("Will try to extract location from query")
            print("Processing, please wait...\n")
            result = await assistant.process_query(full_query)
        
        # Print the result
        print("\nResult:")
        print(result)
    except Exception as e:
        print(f"Error running assistant: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())