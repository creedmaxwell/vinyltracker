from flask import Flask, jsonify, request, g
from db import UsersDB, VinylDB
from session_store import SessionStore
import os
from dotenv import load_dotenv
import requests
from pathlib import Path
from agent.vector_store_components.tools.vector_store import VinylRetriever
from agent.agent import build_agent
from spotify_auth import spotify_auth, init_spotify_auth

app = Flask(__name__)
session_store = SessionStore()

spotify_auth._session_store = session_store

load_dotenv()

# sessions

def load_session_data():
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith('Bearer '):
        session_id = auth_header.removeprefix('Bearer ')
    else:
        session_id = None
    
    if session_id:
        session_data = session_store.get_session_data(session_id)
    else:
        session_data = None
    
    if session_id == None or session_data == None:
        session_id = session_store.create_session()
        session_data = session_store.get_session_data(session_id)

    g.session_id = session_id
    g.session_data = session_data
    #print("Session ID:", g.session_id)
    #print("Session Data:", g.session_data)

@app.before_request
def before_request_function():
    if request.method == "OPTIONS":
        response = app.response_class("", status=204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
    load_session_data()
    
@app.after_request
def after_request_function(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.after_request
def save_session(response):
    if hasattr(g, 'session_id') and hasattr(g, 'session_data'):
        session_store.save_session_data(g.session_id, g.session_data)
    return response

@app.route("/sessions", methods=["GET"])
def retrieveSession():
    return {
        "id": g.session_id,
        "data": g.session_data
    }

@app.route("/sessions/auth", methods=["POST"])
def validate_user():
    username = request.form["username"]
    password = request.form["password"]
    db = UsersDB('trackerdb.db')
    if db.validatePassword(username, password):
        print("Valid")
        g.session_data["user_id"] = username
        session_store.save_session_data(g.session_id, g.session_data)
        return jsonify({"message": f"Valid {username}"}), 200, {"Access-Control-Allow-Origin": "*"}
    else:
        print("Not valid")
        return jsonify({"error": "Invalid credentials"}), 401, {"Access-Control-Allow-Origin": "*"}

init_spotify_auth(session_store)
app.register_blueprint(spotify_auth)

# --- proxy search ---

@app.route('/api/discogs/search', methods=["GET"])
def proxy_discogs_search():
    if "user_id" not in g.session_data:
        return jsonify({"error": "Unauthenticated"}), 401
    
    # Get query parameters from request
    query = request.args.get('query', '')
    search_type = request.args.get('type', '')
    
    # Construct Discogs API URL
    discogs_url = 'https://api.discogs.com/database/search'
    
    # Make request to Discogs with your API key
    response = requests.get(
        discogs_url,
        params={
            search_type: query,
            'token': os.getenv('DISCOGS_API_KEY')
        }
    )
    
    return response.json(), response.status_code

@app.route('/api/discogs/releases', methods=["GET"])
def proxy_discogs_releases_search():
    if "user_id" not in g.session_data:
        return jsonify({"error": "Unauthenticated"}), 401
    
    release_id = request.args.get('url', '')
    if not release_id:
        return jsonify({"error": "No release id provided"}), 400, {"Access-Control-Allow-Origin": "*"}
    
    # Construct Discogs API URL
    discogs_url = f'https://api.discogs.com/releases/{release_id}'
    token = os.getenv('DISCOGS_API_KEY')

    headers = {
        "User-Agent": "VinylTracker/1.0"
    }
    
    if token:
        headers["Authorization"] = f"Discogs token={token}"

    try:
        resp = requests.get(discogs_url, headers=headers, timeout=10)
        # pass through Discogs response and status
        return resp.json(), resp.status_code, {"Access-Control-Allow-Origin": "*"}
    except Exception as e:
        return jsonify({"error": f"Error fetching release from Discogs: {e}"}), 500, {"Access-Control-Allow-Origin": "*"}

# ---- agent ----

def format_history_as_prompt(history, user_query):
    """
    Convert structured history + latest user query to a single text prompt.
    This is simple and effective. You can later change to JSON or other formats.
    """
    lines = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        # Add role prefix
        if role == "user":
            lines.append(f"User: {content}")
        elif role == "assistant":
            lines.append(f"Assistant: {content}")
        else:
            lines.append(f"{role.capitalize()}: {content}")
    # append the current user query at the end
    lines.append(f"User: {user_query}")
    prompt = "\n".join(lines)
    return prompt

@app.route('/api/assistant/search', methods=['POST'])
def search_collection():
    if "user_id" not in g.session_data:
        return jsonify({"error": "Unauthenticated"}), 401
    
    user_id = g.session_data["user_id"]
    query = request.json.get('query')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        results = vinyl_retriever.retrieve(query, user_id)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/assistant/query', methods=['POST'])
def query_assistant():
    if "user_id" not in g.session_data:
        return jsonify({"error": "Unauthenticated"}), 401
    
    user_id = g.session_data["user_id"]
    query = request.json.get('query')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Check if Spotify is connected
        spotify_token = g.session_data.get('spotify_access_token')
        has_spotify = "Yes" if spotify_token else "No"

        # 1. fetch recent history for this session
        history = session_store.get_history(g.session_id, limit=10)  # last 10 messages
        
        # 2. store the user's current message into session history
        g.session_data = session_store.append_message(g.session_id, "user", query)
        
        # 3. format the prompt string that will be passed to agent.run()
        prompt = format_history_as_prompt(history, query)
        # optionally include user_id in the prompt so tools know which user to query
        prompt = f"USER_ID: {user_id}\nSPOTIFY_CONNECTED: {has_spotify}\n\n" + prompt
        
        # 4. build agent and run - agent.run expects a string prompt
        agent = build_agent()
        response = agent.run(prompt)

        # ensure response is a string
        if isinstance(response, dict):
            # if your agent framework returns structured output, extract text
            response_text = response.get("text") or str(response)
        else:
            response_text = str(response)
        
        # 5. save assistant response to history
        g.session_data = session_store.append_message(g.session_id, "assistant", response_text)
        
        return jsonify({"response": response_text}), 200
    except Exception as e:
        print(f"Agent error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Agent error: {str(e)}"}), 500

# ---- vector store -----
persist_dir = Path(__file__).parent / "agent" / "data" / "vector_store"
vinyl_retriever = VinylRetriever(persist_dir)

#vinyl methods

@app.route('/vinyl', methods=["GET"])
def get_user_vinyl():
    db = VinylDB("trackerdb.db")
    print("VINYL GET: ")
    print(g.session_data)
    if "user_id" not in g.session_data:
        print("They are not authenticated")
        return jsonify({"error": "Unauthenticated"}), 401, {"Access-Control-Allow-Origin": "*"}
    #print(request.headers)
    user_id = g.session_data["user_id"]
    url = request.args.get("url")
    if url:
        record = db.readVinylRecordBarcode(url, user_id)
        if record:
            return jsonify(record), 200, {"Access-Control-Allow-Origin": "*"}
        else:
            return jsonify({"error": "Not found"}), 404, {"Access-Control-Allow-Origin": "*"}
    else:
        allRecords = db.readAllVinylRecords(user_id)
        return jsonify(allRecords), 200, {"Access-Control-Allow-Origin": "*"}

@app.route('/vinyl', methods=["POST"])
def add_new_vinyl():

    if "user_id" not in g.session_data:
        print("User is not logged in")
        return jsonify({"error": "Unauthenticated"}), 401, {"Access-Control-Allow-Origin": "*"}
    
    db = VinylDB("trackerdb.db")
    print("The form data is: ", request.form)
    url = request.form["url"]
    album = request.form["album"]
    artist = request.form["artist"]
    cover_image = request.form["cover_image"]
    genre = request.form["genre"]
    format = request.form["format"]
    user_id = g.session_data["user_id"]

    db.saveVinylRecord(url, album, artist, cover_image, genre, format, user_id)

    # Add to vector store
    record = {
        'url': url,
        'album': album,
        'artist': artist,
        'genre': genre,
        'format': format,
        'user_id': user_id
    }

    record_id = f"{user_id}_{url.split('/')[-1]}" # Use Discogs ID as unique identifier
    vinyl_retriever.add_record(record, record_id)

    return "Created", 201, {"Access-Control-Allow-Origin": "*"}

@app.route('/vinyl', methods=["DELETE"])
def delete_vinyl():
    if "user_id" not in g.session_data:
        print("User is not logged in")
        return jsonify({"error": "Unauthenticated"}), 401, {"Access-Control-Allow-Origin": "*"}
    
    db = VinylDB("trackerdb.db")
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No url provided"}), 400
    
    user_id = g.session_data["user_id"]

    # Check if record exists for the user
    existing_record = db.readVinylRecordURL(url, user_id)
    if not existing_record:
        return jsonify({"error": "Record not found for this user"}), 404

    db.deleteVinylRecord(url, user_id)

    # Delete from vector store
    record_id = f"{user_id}_{url.split('/')[-1]}"
    try:
        # Get the record from vector store first to verify ownership
        result = vinyl_retriever._collection.get(
            ids=[record_id],
            where={"user_id": user_id}
        )
        
        if not result['ids']:
            return jsonify({"error": "Record not found or unauthorized"}), 404

        # Delete from SQLite
        db = VinylDB("trackerdb.db")
        db.deleteVinylRecord(url, user_id)

        # Delete from vector store
        vinyl_retriever._collection.delete(
            ids=[record_id],
            where={"user_id": user_id}
        )

    except Exception as e:
        print(f"Error deleting from vector store: {e}")
        return jsonify({"error": "Error deleting record"}), 500

    return "", 204, {"Access-Control-Allow-Origin": "*"}

# wishlist methods
@app.route('/wishlist', methods=["GET"])
def get_user_wishlist():
    db = VinylDB("trackerdb.db")
    print("VINYL GET: ")
    print(g.session_data)
    if "user_id" not in g.session_data:
        print("They are not authenticated")
        return jsonify({"error": "Unauthenticated"}), 401, {"Access-Control-Allow-Origin": "*"}
    #print(request.headers)
    user_id = g.session_data["user_id"]
    url = request.args.get("url")
    if url:
        record = db.readWishlistRecordBarcode(url, user_id)
        if record:
            return jsonify(record), 200, {"Access-Control-Allow-Origin": "*"}
        else:
            return jsonify({"error": "Not found"}), 404, {"Access-Control-Allow-Origin": "*"}
    else:
        allRecords = db.readAllWishlistRecords(user_id)
        return jsonify(allRecords), 200, {"Access-Control-Allow-Origin": "*"}

@app.route('/wishlist', methods=["POST"])
def add_new_wishlist():
    if "user_id" not in g.session_data:
        print("User is not logged in")
        return jsonify({"error": "Unauthenticated"}), 401, {"Access-Control-Allow-Origin": "*"}
    
    db = VinylDB("trackerdb.db")
    print("The form data is: ", request.form)
    url = request.form["url"]
    album = request.form["album"]
    artist = request.form["artist"]
    cover_image = request.form["cover_image"]
    genre = request.form["genre"]
    format = request.form["format"]
    user_id = g.session_data["user_id"]

    db.saveWishlistRecord(url, album, artist, cover_image, genre, format, user_id)
    return "Created", 201, {"Access-Control-Allow-Origin": "*"}

@app.route('/wishlist', methods=["DELETE"])
def delete_wishlist_record():
    if "user_id" not in g.session_data:
        print("User is not logged in")
        return jsonify({"error": "Unauthenticated"}), 401, {"Access-Control-Allow-Origin": "*"}
    
    db = VinylDB("trackerdb.db")
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No url provided"}), 400
    
    user_id = g.session_data["user_id"]

    db.deleteWishlistRecord(url, user_id)
    return "", 204, {"Access-Control-Allow-Origin": "*"}

# user registration
@app.route('/users', methods=["POST"])
def add_new_user():
    db = UsersDB("trackerdb.db")
    print("The form data is: ", request.form)
    username = request.form["username"]
    password = request.form["password"]

    db.saveRecord(username, password)
    return "Created", 201, {"Access-Control-Allow-Origin": "*"}

@app.route("/sessions", methods=["DELETE"])
def logout_user():
    if "user_id" not in g.session_data:
        return "Unauthenticated", 401, {"Access-Control-Allow-Origin": "*"}
    
    del g.session_data["user_id"]
    return "Deleted", 200, {"Access-Control-Allow-Origin": "*"}

def run():
    app.run(port=8080, host='0.0.0.0')

if __name__ == '__main__':
    run()