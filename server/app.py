from flask import Flask, jsonify, request, g
from db import UsersDB, VinylDB
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
    barcode = request.form["barcode"]
    album = request.form["album"]
    artist = request.form["artist"]
    user_id = g.session_data["user_id"]

    db.saveVinylRecord(url, barcode, album, artist, user_id)
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

    db.deleteVinylRecord(url, user_id)
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
    barcode = request.form["barcode"]
    album = request.form["album"]
    artist = request.form["artist"]
    user_id = g.session_data["user_id"]

    db.saveWishlistRecord(url, barcode, album, artist, user_id)
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