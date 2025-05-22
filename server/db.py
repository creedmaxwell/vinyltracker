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

    def saveVinylRecord(self, barcode, user_id):
        data = [barcode, user_id]
        cmd = "INSERT INTO vinyl (barcode, user_id) VALUES (?, ?)"
        self.cursor.execute(cmd, data)
        self.conn.commit()

    def readAllVinylRecords(self, user_id):
        cmd = "SELECT * FROM vinyl WHERE user_id = ?"
        self.cursor.execute(cmd, [user_id])
        vinyl = self.cursor.fetchall()
        return vinyl
    
    def deleteVinylRecord(self, barcode, user_id):
       data = [barcode, user_id]
       cmd = "DELETE FROM vinyl WHERE ( barcode = ? AND user_id = ? )"
       self.cursor.execute(cmd, data)
       self.conn.commit()

    def updateVinylRecord(self, id, barcode):
       data = [barcode, id]
       cmd = "UPDATE vinyl SET barcode = ? WHERE id = ?"
       self.cursor.execute(cmd, data)
       self.conn.commit()