import os
import asyncio
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
from functools import wraps
import logging
from sqlalchemy.exc import SQLAlchemyError

from assistant import LocationAssistant
from models import AppConfig

# Load environment variables
load_dotenv()

# Database credentials from environment variables
db_host = os.environ.get('DB_HOST', '')
db_name = os.environ.get('DB_NAME', '')
db_user = os.environ.get('DB_USER', '')
db_password = os.environ.get('DB_PASSWORD', '')
db_port = os.environ.get('DB_PORT', 5432)

# Get configuration
config = AppConfig.from_env()

# Initialize the assistant
assistant = LocationAssistant(
    openai_api_key=config.openai_api_key,
    maps_api_key=config.maps_api_key,
    serper_api_key=config.serper_api_key
)

# Create Flask app
app = Flask(__name__, static_folder='static')

# Configure SQLAlchemy
# Format: postgresql://username:password@host:port/database_name
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@/{db_name}?host=/cloudsql/{db_host}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    profile_picture = db.Column(db.String)

# Define FinalResponse model for storing query responses
class FinalResponse(db.Model):
    __tablename__ = 'final_response'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('user.user_id'), nullable=True)
    query = db.Column(db.Text, nullable=False)
    model_response = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Helper function to run async functions in Flask
def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

# Create all tables
with app.app_context():
    db.create_all()

# Serve the main page
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/user', methods=['POST'])
def create_or_update_user():
    try:
        data = request.get_json()
        user_id = data.get('id')
        name = data.get('name')
        email = data.get('email')
        profile_picture = data.get('image')

        logging.info(f"Received user data: user_id={user_id}, name={name}, email={email}")

        if not all([user_id, name, email]):  # Basic validation
            logging.warning("Incomplete user data received.")
            return jsonify({'success': False, 'message': 'Incomplete data'}), 400

        # Check if user exists
        existing_user = User.query.filter_by(user_id=user_id).first()

        if existing_user:
            logging.info(f"User with user_id {user_id} already exists. Updating information.")
            # Update user information
            existing_user.name = name
            existing_user.profile_picture = profile_picture
        else:
            logging.info(f"User with user_id {user_id} does not exist. Inserting new user.")
            # Create new user
            new_user = User(
                user_id=user_id,
                name=name,
                email=email,
                profile_picture=profile_picture
            )
            db.session.add(new_user)

        db.session.commit()
        logging.info("Transaction committed successfully.")

        return jsonify({'success': True})

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error: {str(e)}")
        return jsonify({'success': False, 'message': f"Database error: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({'success': False, 'message': f"Unexpected error: {str(e)}"}), 500
    
def store_final_response(user_id, query, model_response, latitude, longitude):
    """
    Store the final response using SQLAlchemy instead of raw psycopg2
    """
    try:
        # Create a new FinalResponse record
        new_response = FinalResponse(
            user_id=user_id,
            query=query,
            model_response=model_response,
            latitude=latitude,
            longitude=longitude
        )
        
        # Add to session and commit
        db.session.add(new_response)
        db.session.commit()
        logging.info(f"Successfully stored response for user {user_id}")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error storing response: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error storing response: {str(e)}")

@app.route('/api/process-query', methods=['POST'])
@async_route
async def process_query():
    """API endpoint to process location-based queries."""
    try:
        # Get data from the request
        data = request.json
        
        # Extract the user query (required)
        if 'query' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No query provided'
            }), 400
        
        query = data.get('query')
        user_id = data.get('userId')
        logging.info(f"Received query: {query} from user: {user_id}")
        
        # Process the query - the location should be embedded in the query
        try:
            # We'll pass the raw query to the assistant which will extract location information
            model_response = await assistant.process_query(query)
            
            # Extract latitude and longitude from the assistant's response
            # In a real implementation, you might want to get these from the location_parser
            # For now, using the simplified approach
            latitude = assistant.latitude if hasattr(assistant, 'latitude') else None
            longitude = assistant.longitude if hasattr(assistant, 'longitude') else None
            
            # Check if we used no valid address (indicating no location was found)
            if "no valid address" in model_response.lower():
                return jsonify({
                    'status': 'warning',
                    'message': 'No location information found in query',
                    'result': "The address was not found. Kindly include the address in your query to proceed."
                })
            
            # Store the response in the database
            store_final_response(user_id, query, model_response, latitude, longitude)
            
            # Return the successful result
            return jsonify({
                'status': 'success',
                'result': model_response
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error processing query: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Check for required API keys
    if not config.openai_api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please create a .env file based on .env.example and add your API keys.")
    else:
        # Run the app
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=True)