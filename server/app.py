from flask import Flask, jsonify, request, g
from db import UsersDB
from passlib.hash import bcrypt
from session_store import SessionStore

app = Flask(__name__)
session_store = SessionStore()

# sessions

def load_session_data():
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith('Bearer '):
        session_id = auth_header.removeprefix('Bearer ')
    else:
        session_id = None
    
    if session_id:
        session_data = session_store.get_session_data(session_id)
        print("The session data is", session_data)
    else:
        session_data = None
    
    if session_id == None or session_data == None:
        session_id = session_store.create_session()
        session_data = session_store.get_session_data(session_id)

    g.session_id = session_id
    g.session_data = session_data
    print("Session ID:", g.session_id)
    print("Session Data:", g.session_data)

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
    db = UsersDB('artists.db')
    if db.validatePassword(username, password):
        print("Valid")
        g.session_data["user_id"] = username
        return jsonify({"message": f"Valid {username}"}), 200, {"Access-Control-Allow-Origin": "*"}
    else:
        print("Not valid")
        return jsonify({"error": "Invalid credentials"}), 401, {"Access-Control-Allow-Origin": "*"}
    
#artist methods

@app.route('/artists', methods=["GET"])
def get_artists():
    db = ArtistsDB("artists.db")
    if "user_id" not in g.session_data:
        print("They are not authenticated")
        return jsonify({"error": "Unauthenticated"}), 401, {"Access-Control-Allow-Origin": "*"}
    print(request.headers)
    allRecords = db.readAllArtistRecords()
    return jsonify(allRecords), 200, {"Access-Control-Allow-Origin": "*"}

@app.route('/artists', methods=["POST"])
def add_new_artist():
    if "user_id" not in g.session_data:
        print("User is not logged in")
        return jsonify({"error": "Unauthenticated"}), 401, {"Access-Control-Allow-Origin": "*"}
    
    db = ArtistsDB("artists.db")
    print("The form data is: ", request.form)
    name = request.form["name"]
    rating = request.form["rating"]
    genre = request.form["genre"]
    description = request.form["description"]

    db.saveArtistRecord(name, rating, genre, description)
    return "Created", 201, {"Access-Control-Allow-Origin": "*"}

#song methods

@app.route('/songs/<artist_name>', methods=["GET"])
def get_songs(artist_name):
    db = ArtistsDB("artists.db")
    allSongs = db.readAllSongRecords(artist_name)
    artistSongs = [song for song in allSongs if song.get("artist") == artist_name]
    return jsonify(artistSongs), 200, {"Access-Control-Allow-Origin": "*"}

@app.route('/songs', methods=["POST"])
def add_new_song():
    db = ArtistsDB("artists.db")
    print("The form data is: ", request.form)
    artist = request.form["artist"]
    song = request.form["song"]
    rating = request.form["rating"]
    description = request.form["description"]
    
    db.saveSongRecord(song, artist, description, rating)
    return "Created", 201, {"Access-Control-Allow-Origin": "*"}

@app.route('/songs/<int:id>', methods = ["OPTIONS"])
def do_preflight(id):
    print("This is the preflight")

    return '', 204, {"Access-Control-Allow-Origin": "*", 
                     "Access-Control-Allow-Methods": "PUT, DELETE", 
                     "Access-Control-Allow-Headers": "Content-Type"}

@app.route('/songs/<int:id>', methods=["DELETE"])
def delete_trail(id):
    db = ArtistsDB("artists.db")
    db.deleteSongRecord(id)
    return "Record Deleted", 200, {"Access-Control-Allow-Origin": "*"}

@app.route("/songs/<int:id>", methods = ["PUT"])
def update_trail(id):
    db = ArtistsDB("artists.db")
    name = request.form["name"]
    rating = request.form["rating"]
    description = request.form["description"]
    db.updateSongRecord(id, name, description, rating)
    return "Saved", 201, {"Access-Control-Allow-Origin": "*"}

# user registration
@app.route('/users', methods=["POST"])
def add_new_user():
    db = UsersDB("artists.db")
    print("The form data is: ", request.form)
    firstname = request.form["firstname"]
    lastname = request.form["lastname"]
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    db.saveRecord(firstname, lastname, username, email, password)
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