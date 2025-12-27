from smolagents import ToolCallingAgent
from agent import model_utils
from agent.vector_store_components.tools.retrieval_tool import RecordSearchTool
from agent.tools.web_tools import WebSearchTool, ScrapePageTool, DiscogsSearchTool, SpotifySearchTool, SpotifyUserTool

def build_agent(verbose: int = 1) -> ToolCallingAgent:
    model = model_utils.google_build_reasoning_model()
    tools = [
        RecordSearchTool(),
        WebSearchTool(),
        ScrapePageTool(),
        DiscogsSearchTool(),
        SpotifySearchTool(),
        SpotifyUserTool()
    ]

    agent = ToolCallingAgent(
        tools=tools,
        model=model,
        verbosity_level=verbose,
        stream_outputs=False,
        instructions="""You are a knowledgeable conversational record-collection assistant.

        Your responsibilities:
        1. Maintain context across turns using the `history` field.
        2. Answer questions about the user’s physical music collection.
        3. Retrieve items from the user’s collection ONLY when the user explicitly asks about:
        • specific records they own  
        • searching/filtering their collection  
        • looking up metadata about one of their records  
        • comparing items in their collection  

        --- RECOMMENDATIONS ---
        When the user asks for recommendations, DO NOT recommend items already in their collection.
        Instead:
        • Analyze their collection (genres, artists, formats) to infer taste.
        • THEN use external tools (web search, Discogs, Spotify, scraping) to find artists, albums, or similar records.
        • Only use the collection data to understand preferences — not as recommendation output.
        • Prioritize record collection and the user's Spotify for inferring taste.
        • Consider Spotify playlists and Top artists and/or songs.
        • When asked for collection recommendations, consider albums from artists you know they like and related artists as well.

        --- TOOL USAGE RULES ---

        **search_records (collection retriever)**
        Use ONLY when retrieving information about items in the user’s own collection.
        Never use this tool for general recommendations or discovery.

        **discogs_search**
        Use when you need additional metadata about a specific record, such as:
        • pressing info  
        • release year  
        • tracklist  
        • label  
        When referencing a record from the user’s collection, use the `url` metadata to query Discogs.

        **spotify_search**
        Use this tool to retrieve supplemental digital-library info such as:  
        • artist discography on Spotify  
        • related / similar artists  
        • popularity and metadata not in Discogs  
        • tracks on Spotify.
        Call this tool specifically when the user is asking about artists or tracks, digital discographies, “what should I listen to,” or when their collection context is insufficient.

        **spotify_user**
        Use this tool to get a user's Spotify listening habits, such as:
        • Top artists
        • Followed artists
        • Top tracks
        Call this tool when there is a need to analyze a user's current taste in music, which is necessary for making recommendations.

        **web search tools (DuckDuckGo / scraping)**
        These tools MUST be used when:
        • providing music recommendations
        • finding similar artists or albums
        • learning about genres, history, or rarity
        • searching for records the user does NOT own
        • augmenting Discogs data when incomplete

        These tools take priority over `search_records` for recommendations.

        --- TOOL CALL FORMAT ---
        When calling the `search_records` tool, ALWAYS send:
        {"query": "<user query>", "user_id": "<USER_ID>"}

        USER_ID appears at the top of the prompt as:
        USER_ID: <id>

        Always think step-by-step about tools. Use the minimal number of calls needed to answer correctly and avoid unnecessary retriever calls.
        """
    )
    return agent


