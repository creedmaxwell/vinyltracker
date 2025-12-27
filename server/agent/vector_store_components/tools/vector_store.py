"""ChromaDB-backed retrieval utilities."""

from pathlib import Path
from typing import List

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


class ChromaRetriever:
    """Thin wrapper around a ChromaDB collection that supports semantic search."""

    def __init__(
        self,
        persist_directory: Path,
        collection_name: str,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        max_results: int = 1000,
    ) -> None:
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.max_results = max_results

        self._client = chromadb.PersistentClient(path=str(self.persist_directory))
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=SentenceTransformerEmbeddingFunction(
                model_name=embedding_model
            ),
        )

    def retrieve(self, query: str, user_id:str) -> List[dict]:
        """Return the top-matching documents with metadata.

        Args:
            query: natural-language search string.
            user_id: user identifier to filter results
        """
        if not query:
            raise ValueError("Query must be a non-empty string.")

        # Get all results first
        response = self._collection.query(
            query_texts=[query],
            n_results=self.max_results,
            where={"user_id": user_id}  # Filter by user_id in metadata
        )

        results = []
        for doc, metadata in zip(response['documents'][0], response['metadatas'][0]):
            results.append({
                'document': doc,
                'metadata': metadata
            })

        return results

class VinylRetriever(ChromaRetriever):
    """ChromaDB retriever specialized for vinyl records."""
    def __init__(self, persist_directory, collection_name="vinyl_records"):
        super().__init__(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    def add_record(self, record: dict, record_id: str) -> None:
        """Add a single record to the vector store.
        
        Args:
            record: Dictionary containing record details
            record_id: Unique identifier for the record
        """
        document = f"""
        Album: {record['album']}
        Artist: {record['artist']}
        Genre: {record['genre']}
        Format: {record['format']}
        Owner: {record['user_id']}
        """

        self._collection.add(
            documents=[document],
            metadatas=[{
                'url': record['url'],
                'album': record['album'],
                'artist': record['artist'],
                'genre': record['genre'],
                'format': record['format'],
                'user_id': record['user_id']
            }],
            ids=[record_id]
        )