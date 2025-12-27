"""Smolagents Tool wrapper for the Chroma retriever."""

from smolagents import Tool

from .vector_store import VinylRetriever
from pathlib import Path


class RecordSearchTool(Tool):
    name = "search_records"
    description = (
    "Search ONLY the user's personal vinyl record collection. "
    "Use this tool when the user wants to look up information about records "
    "they already own, filter their collection, check for rarity, or retrieve "
    "metadata about their stored albums. "
    "Do NOT use this tool for recommendations or discovering new artists. "
    "It only returns records that the user personally owns."
    )
    inputs = {
        "query": {"type": "string", "description": "Natural-language question or claim to search for."},
        "user_id": {"type": "string", "description": "User ID to search records for"}
    }
    output_type = "string"

    def __init__(self):
        super().__init__()
        persist_dir = Path(__file__).parent.parent.parent / "data" / "vector_store"
        self.retriever = VinylRetriever(persist_dir)

    def forward(self, query: str, user_id: str) -> str:
        if not user_id:
            return "Error: no user_id provided for search_records tool."
        
        results = self.retriever.retrieve(query, user_id)
        return self._format_results(results)

    def _format_results(self, results):
        response = []
        for result in results:
            metadata = result['metadata']
            response.append(f"""
            Album: {metadata['album']}
            Artist: {metadata['artist']}
            Genre: {metadata['genre']}
            Format: {metadata['format']}
            """)
        return "\n".join(response)