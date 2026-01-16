"""
Tool functions that can be used by agents.

These are callable functions that agents can invoke to interact
with the system (search, file retrieval, etc.)
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.utils.logget_setup import app_logger
from app.services.ai_search.search_service import gemini_search_engine
from app.core.configs.app_config import REPO_STORAGE


# Ensure the search engine loads existing index on module import
_index_loaded = gemini_search_engine.load()
if _index_loaded:
    app_logger.info(f"Loaded existing FAISS index with {len(gemini_search_engine)} documents")
else:
    app_logger.info("No existing FAISS index found - starting fresh")


def search_index(query: str, top_k: int = 5) -> str:
    """
    Search the indexed repository for relevant code context.
    
    Use this tool to find files, functions, classes, and documentation
    that are relevant to the user's query. The search returns semantic
    matches from the indexed codebase.
    
    Args:
        query: The search query describing what you're looking for.
               Be specific - e.g., "authentication module", "database models",
               "API endpoints for user management"
        top_k: Number of results to return (default: 5)
        
    Returns:
        A formatted string containing relevant code context from the repository,
        including file paths, summaries, and code snippets.
        Returns "No relevant context found" if the index is empty or no matches.
    """
    try:
        app_logger.info(f"[TOOL] search_index called with query: {query[:100]}...")
        
        # Check if index has documents
        if len(gemini_search_engine) == 0:
            return "No documents have been indexed yet. Please analyze a repository first."
        
        results = gemini_search_engine.search(query_text=query, top_k=top_k)
        
        if not results:
            return "No relevant context found in the indexed repository for this query."
        
        # Format results for the agent
        formatted_parts = []
        formatted_parts.append(f"Found {len(results)} relevant results:\n")
        
        for i, result in enumerate(results, 1):
            score = result.get("score", 0)
            doc_id = result.get("id", "unknown")
            doc_content = result.get("document", "{}")
            
            # Parse the document content (it's stored as JSON string)
            try:
                if isinstance(doc_content, str):
                    doc = json.loads(doc_content)
                else:
                    doc = doc_content
            except json.JSONDecodeError:
                doc = {"content": doc_content}
            
            file_path = doc.get("file", doc_id)
            summary = doc.get("summary", "")
            purpose = doc.get("purpose", "")
            functions = doc.get("functions", [])
            classes = doc.get("classes", [])
            notes = doc.get("notes", [])
            dependencies = doc.get("dependencies", [])
            
            formatted_parts.append(f"━━━ Result {i} (relevance: {score:.2f}) ━━━")
            formatted_parts.append(f"📁 File: {file_path}")
            
            if purpose:
                formatted_parts.append(f"🎯 Purpose: {purpose}")
            if summary:
                formatted_parts.append(f"📝 Summary: {summary}")
            if functions:
                formatted_parts.append(f"⚙️ Functions: {', '.join(functions[:10])}")
            if classes:
                formatted_parts.append(f"🏗️ Classes: {', '.join(classes[:10])}")
            if dependencies:
                formatted_parts.append(f"🔗 Dependencies: {', '.join(dependencies[:5])}")
            if notes:
                formatted_parts.append(f"📌 Notes: {'; '.join(notes[:3])}")
            
            formatted_parts.append("")  # Empty line between results
        
        return "\n".join(formatted_parts)
        
    except Exception as e:
        app_logger.error(f"[TOOL] Error in search_index: {str(e)}")
        return f"Error searching index: {str(e)}"


def retrieve_code_file(file_path: str, user_id: str = "918262") -> str:
    """
    Retrieve the complete contents of a file from the repository.
    
    Use this tool when you need to see the full content of a specific file
    that was mentioned in search results or by the user.
    
    Args:
        file_path: The path to the file to retrieve (relative or absolute)
        user_id: User ID for locating stored repositories
        
    Returns:
        The complete file contents, or an error message if not found.
    """
    try:
        app_logger.info(f"[TOOL] retrieve_code_file called for: {file_path}")
        
        path = Path(file_path)
        
        # Try direct path first
        if path.exists() and path.is_file():
            max_size = 100_000  # 100KB limit
            if path.stat().st_size > max_size:
                return f"File too large ({path.stat().st_size} bytes). Maximum: {max_size} bytes."
            
            content = path.read_text(encoding="utf-8", errors="replace")
            return f"━━━ {file_path} ━━━\n{content}"
        
        # Try searching in repo storage
        repo_storage = Path(REPO_STORAGE) / str(user_id)
        if repo_storage.exists():
            # Search for the file
            for repo_dir in repo_storage.iterdir():
                if repo_dir.is_dir() and repo_dir.name not in ["chunks", "indexed_file", "llm_response"]:
                    potential_path = repo_dir / file_path
                    if potential_path.exists():
                        content = potential_path.read_text(encoding="utf-8", errors="replace")
                        return f"━━━ {file_path} ━━━\n{content}"
        
        return f"File not found: {file_path}. Please check the path and try again."
        
    except Exception as e:
        app_logger.error(f"[TOOL] Error retrieving file: {str(e)}")
        return f"Error retrieving file: {str(e)}"


def get_indexed_files(folder_id: str = None, user_id: str = "918262") -> str:
    """
    List all files that have been indexed for a repository.
    
    Use this tool to see what files are available in the index
    before searching for specific content.
    
    Args:
        folder_id: Optional folder ID to filter by
        user_id: User ID for locating stored data
        
    Returns:
        A list of indexed files with their basic information.
    """
    try:
        app_logger.info(f"[TOOL] get_indexed_files called")
        
        # Get stats from the search engine
        stats = gemini_search_engine.get_stats()
        
        result = [
            f"Index Statistics:",
            f"- Total indexed documents: {stats['total_documents']}",
            f"- Document store size: {stats['doc_store_size']}",
            f"- Embedding dimension: {stats['dimension']}",
            ""
        ]
        
        # Try to get actual file list from stored data
        llm_response_dir = Path(REPO_STORAGE) / str(user_id) / "llm_response"
        if llm_response_dir.exists():
            for response_file in llm_response_dir.glob("response_*.json"):
                try:
                    data = json.loads(response_file.read_text(encoding="utf-8"))
                    folder = response_file.stem.replace("response_", "")
                    files_index = data.get("files_index", {})
                    
                    result.append(f"\n📁 Repository: {folder}")
                    result.append(f"   Files indexed: {len(files_index)}")
                    
                    for file_path in list(files_index.keys())[:10]:
                        result.append(f"   - {file_path}")
                    
                    if len(files_index) > 10:
                        result.append(f"   ... and {len(files_index) - 10} more files")
                        
                except Exception:
                    continue
        
        return "\n".join(result)
        
    except Exception as e:
        app_logger.error(f"[TOOL] Error getting indexed files: {str(e)}")
        return f"Error getting indexed files: {str(e)}"
