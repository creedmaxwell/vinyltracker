#!/usr/bin/env python3
from pathlib import Path
import sqlite3
from tools.vector_store import VinylRetriever

def ingest_records_to_vectorstore():
    # Connect to your SQLite database
    db_path = Path(__file__).parent.parent.parent /"trackerdb.db"
    print(f"Attempting to connect to database at: {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all records with their metadata
    cursor.execute("""
        SELECT r.*, u.username 
        FROM records r 
        JOIN users u ON r.user_id = u.username
    """)
    records = cursor.fetchall()

    # Initialize vector store
    persist_dir = Path(__file__).parent.parent / "data" / "vector_store"
    retriever = VinylRetriever(persist_dir)

    # Prepare documents for ingestion
    for record in records:
        # Create a rich text description for each record
        document = f"""
        Album: {record['album']}
        Artist: {record['artist']}
        Genre: {record['genre']}
        Format: {record['format']}
        Owner: {record['username']}
        """

        # Store in vector database with metadata
        retriever._collection.add(
            documents=[document],
            metadatas=[{
                'url': record['url'],
                'album': record['album'],
                'artist': record['artist'],
                'genre': record['genre'],
                'format': record['format'],
                'user_id': record['username']
            }],
            ids=[str(record['url'])]
        )

if __name__ == "__main__":
    ingest_records_to_vectorstore()