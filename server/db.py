import json
import sqlite3
from passlib.hash import bcrypt

def dict_factory(cursor, row):
    fields = []
    # Extract column names from cursor description
    for column in cursor.description:
        fields.append(column[0])

    # Create a dictionary where keys are column names and values are row values
    result_dict = {}
    for i in range(len(fields)):
        result_dict[fields[i]] = row[i]

    return result_dict

class UsersDB:
    def __init__(self, filename):
        #connect to the database
        self.conn = sqlite3.connect(filename)
        #initialize cursor
        self.conn.row_factory = dict_factory
        self.cursor = self.conn.cursor()

    def saveRecord(self, username, password):
        password = bcrypt.hash(password)
        data = [username, password]
        cmd = "INSERT INTO users (username, password) VALUES (?, ?)"
        self.cursor.execute(cmd, data)
        self.conn.commit()

    def readAllRecords(self):
        cmd = "SELECT * FROM users"
        self.cursor.execute(cmd)
        users = self.cursor.fetchall()
        return users
    
    def deleteRecord(self, id):
       data = [id]
       cmd = "DELETE FROM users WHERE id = ?"
       self.cursor.execute(cmd, data)
       self.conn.commit()

    def updateRecord(self, id, name, description, rating, genre):
       data = [name, description, rating, genre, id]
       cmd = "UPDATE artists SET artist = ?, description = ?, rating = ?, genre = ? WHERE id = ?"
       self.cursor.execute(cmd, data)
       self.conn.commit()
    
    def validatePassword(self, username, password):
       data = [username]
       cmd = "SELECT * FROM users WHERE username=?"
       self.cursor.execute(cmd, data)
       user = self.cursor.fetchone()
       if user:
          print("Retrieved password hash:", user['password'])  # Debugging
          if bcrypt.verify(password, user['password']):
            return True
       return False
    
class VinylDB:
    def __init__(self, filename):
        #connect to the database
        self.conn = sqlite3.connect(filename)
        #initialize cursor
        self.conn.row_factory = dict_factory
        self.cursor = self.conn.cursor()

    def saveVinylRecord(self, url, barcode, album, artist, user_id):
        data = [url, barcode, album, artist, user_id]
        cmd = "INSERT INTO records (url, barcode, album, artist, user_id) VALUES (?, ?, ?, ?, ?)"
        self.cursor.execute(cmd, data)
        self.conn.commit()

    def saveWishlistRecord(self, url, barcode, album, artist, user_id):
        data = [url, barcode, album, artist, user_id]
        cmd = "INSERT INTO wishlist (url, barcode, album, artist, user_id) VALUES (?, ?, ?, ?, ?)"
        self.cursor.execute(cmd, data)
        self.conn.commit()

    def readAllVinylRecords(self, user_id):
        cmd = "SELECT * FROM records WHERE user_id = ?"
        self.cursor.execute(cmd, [user_id])
        vinyl = self.cursor.fetchall()
        return vinyl
    
    def readAllWishlistRecords(self, user_id):
        cmd = "SELECT * FROM wishlist WHERE user_id = ?"
        self.cursor.execute(cmd, [user_id])
        vinyl = self.cursor.fetchall()
        return vinyl
    
    def readVinylRecordArtist(self, artist, user_id):
        data = [artist, user_id]
        cmd = "SELECT * FROM records WHERE ( artist = ? AND user_id = ? )"
        self.cursor.execute(cmd, data)
        vinyl = self.cursor.fetchall()
        return vinyl
    
    def readWishlistRecordArtist(self, artist, user_id):
        data = [artist, user_id]
        cmd = "SELECT * FROM wishlist WHERE ( artist = ? AND user_id = ? )"
        self.cursor.execute(cmd, data)
        vinyl = self.cursor.fetchall()
        return vinyl

    def readVinylRecordBarcode(self, barcode, user_id):
        data = [barcode, user_id]
        cmd = "SELECT * FROM records WHERE ( barcode = ? AND user_id = ? )"
        self.cursor.execute(cmd, data)
        vinyl = self.cursor.fetchall()
        return vinyl
    
    def readWishlistRecordBarcode(self, barcode, user_id):
        data = [barcode, user_id]
        cmd = "SELECT * FROM wishlist WHERE ( barcode = ? AND user_id = ? )"
        self.cursor.execute(cmd, data)
        vinyl = self.cursor.fetchall()
        return vinyl
    
    def readVinylRecordURL(self, url, user_id):
        data = [url, user_id]
        cmd = "SELECT * FROM records WHERE ( url = ? AND user_id = ? )"
        self.cursor.execute(cmd, data)
        vinyl = self.cursor.fetchall()
        return vinyl
    
    def readWishlistRecordURL(self, url, user_id):
        data = [url, user_id]
        cmd = "SELECT * FROM wishlist WHERE ( url = ? AND user_id = ? )"
        self.cursor.execute(cmd, data)
        vinyl = self.cursor.fetchall()
        return vinyl
    
    def deleteVinylRecord(self, url, user_id):
       url = 'https://api.discogs.com/releases/' + url
       data = [url, user_id]
       cmd = "DELETE FROM records WHERE rowid = ( SELECT rowid FROM records WHERE url = ? AND user_id = ? LIMIT 1)"
       self.cursor.execute(cmd, data)
       self.conn.commit()

    def deleteWishlistRecord(self, url, user_id):
       url = 'https://api.discogs.com/releases/' + url
       data = [url, user_id]
       cmd = "DELETE FROM wishlist WHERE rowid = ( SELECT rowid FROM wishlist WHERE url = ? AND user_id = ? LIMIT 1)"
       self.cursor.execute(cmd, data)
       self.conn.commit()

    def updateVinylRecord(self, id, barcode):
       data = [barcode, id]
       cmd = "UPDATE records SET barcode = ? WHERE id = ?"
       self.cursor.execute(cmd, data)
       self.conn.commit()