"""
Tool functions that can be used by agents.

These are callable functions that agents can invoke to interact
with the system (search, file retrieval, etc.)
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.utils.logget_setup import ai_logger
from app.services.ai_search.search_service import gemini_search_engine
from app.core.configs.app_config import REPO_STORAGE


# Track currently loaded folder_id to avoid reloading same index
_current_folder_id: str | None = None

def load_index_for_folder(folder_id: str | None = None) -> bool:
    """
    Load the FAISS index for a specific folder.
    If already loaded for this folder, returns True without reloading.
    
    Args:
        folder_id: The folder ID to load index for. If None, loads default global index.
        
    Returns:
        True if index loaded successfully, False otherwise.
    """
    global _current_folder_id
    
    # Skip if already loaded for this folder
    if _current_folder_id == folder_id and len(gemini_search_engine) > 0:
        ai_logger.debug(f"[INDEX] Already loaded for folder_id={folder_id}")
        return True
    
    ai_logger.debug(f"[INDEX] Loading index for folder_id={folder_id}")
    success = gemini_search_engine.load(folder_id)
    
    if success:
        _current_folder_id = folder_id
        ai_logger.debug(f"[INDEX] Loaded {len(gemini_search_engine)} documents for folder_id={folder_id}")
    else:
        ai_logger.warning(f"[INDEX] No index found for folder_id={folder_id}")
        _current_folder_id = None
        
    return success



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
    ai_logger.debug(f"[TOOL:search_index] Called with query='{query[:80]}...', top_k={top_k}")
    
    try:
        # Check if index has documents
        doc_count = len(gemini_search_engine)
        ai_logger.debug(f"[TOOL:search_index] Index contains {doc_count} documents")
        
        if doc_count == 0:
            ai_logger.warning("[TOOL:search_index] Index is empty, no documents indexed")
            return "No documents have been indexed yet. Please analyze a repository first."
        
        ai_logger.debug(f"[TOOL:search_index] Executing search...")
        results = gemini_search_engine.search(query_text=query, top_k=top_k)
        
        if not results:
            ai_logger.debug(f"[TOOL:search_index] No relevant results found for query")
            return "No relevant context found in the indexed repository for this query."
        
        ai_logger.debug(f"[TOOL:search_index] Found {len(results)} results")
        
        # Format results for the agent
        formatted_parts = []
        formatted_parts.append(f"Found {len(results)} relevant results:\n")
        
        for i, result in enumerate(results, 1):
            score = result.get("score", 0)
            doc_id = result.get("id", "unknown")
            doc_content = result.get("document", "{}")
            
            ai_logger.debug(f"[TOOL:search_index] Result {i}: score={score:.3f}, doc_id={doc_id}")
            
            # Parse the document content (it's stored as JSON string)
            try:
                if isinstance(doc_content, str):
                    doc = json.loads(doc_content)
                else:
                    doc = doc_content
            except json.JSONDecodeError as e:
                ai_logger.warning(f"[TOOL:search_index] Failed to parse doc content as JSON: {str(e)}")
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
        
        ai_logger.debug(f"[TOOL:search_index] Returning formatted results")
        return "\n".join(formatted_parts)
        
    except Exception as e:
        ai_logger.error(f"[TOOL:search_index] Error during search: {str(e)}", exc_info=True)
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
    ai_logger.debug(f"[TOOL:retrieve_code_file] Called with file_path='{file_path}', user_id='{user_id}'")
    
    try:
        path = Path(file_path)
        
        # Try direct path first
        if path.exists() and path.is_file():
            ai_logger.debug(f"[TOOL:retrieve_code_file] Found file at direct path: {path}")
            max_size = 100_000  # 100KB limit
            file_size = path.stat().st_size
            
            if file_size > max_size:
                ai_logger.warning(f"[TOOL:retrieve_code_file] File too large: {file_size} bytes (max: {max_size})")
                return f"File too large ({file_size} bytes). Maximum: {max_size} bytes."
            
            ai_logger.debug(f"[TOOL:retrieve_code_file] Reading file ({file_size} bytes)...")
            content = path.read_text(encoding="utf-8", errors="replace")
            ai_logger.debug(f"[TOOL:retrieve_code_file] Successfully read {len(content)} characters")
            return f"━━━ {file_path} ━━━\n{content}"
        
        # Try searching in repo storage
        ai_logger.debug(f"[TOOL:retrieve_code_file] File not found at direct path, searching in repo storage...")
        repo_storage = Path(REPO_STORAGE) / str(user_id)
        
        if repo_storage.exists():
            ai_logger.debug(f"[TOOL:retrieve_code_file] Searching in user storage: {repo_storage}")
            # Search for the file
            for repo_dir in repo_storage.iterdir():
                if repo_dir.is_dir() and repo_dir.name not in ["chunks", "indexed_file", "llm_response"]:
                    potential_path = repo_dir / file_path
                    if potential_path.exists():
                        ai_logger.debug(f"[TOOL:retrieve_code_file] Found file at: {potential_path}")
                        content = potential_path.read_text(encoding="utf-8", errors="replace")
                        ai_logger.debug(f"[TOOL:retrieve_code_file] Successfully read {len(content)} characters")
                        return f"━━━ {file_path} ━━━\n{content}"
        else:
            ai_logger.debug(f"[TOOL:retrieve_code_file] Repo storage not found at: {repo_storage}")
        
        ai_logger.warning(f"[TOOL:retrieve_code_file] File not found: {file_path}")
        return f"File not found: {file_path}. Please check the path and try again."
        
    except Exception as e:
        ai_logger.error(f"[TOOL:retrieve_code_file] Error retrieving file: {str(e)}", exc_info=True)
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
    ai_logger.debug(f"[TOOL:get_indexed_files] Called with folder_id='{folder_id}', user_id='{user_id}'")
    
    try:
        # Get stats from the search engine
        stats = gemini_search_engine.get_stats()
        ai_logger.debug(f"[TOOL:get_indexed_files] Index stats: {stats}")
        
        result = [
            f"Index Statistics:",
            f"- Total indexed documents: {stats['total_documents']}",
            f"- Document store size: {stats['doc_store_size']}",
            f"- Embedding dimension: {stats['dimension']}",
            ""
        ]
        
        # Try to get actual file list from stored data
        llm_response_dir = Path(REPO_STORAGE) / str(user_id) / "llm_response"
        ai_logger.debug(f"[TOOL:get_indexed_files] Checking for LLM responses at: {llm_response_dir}")
        
        if llm_response_dir.exists():
            response_files = list(llm_response_dir.glob("response_*.json"))
            ai_logger.debug(f"[TOOL:get_indexed_files] Found {len(response_files)} response files")
            
            for response_file in response_files:
                try:
                    data = json.loads(response_file.read_text(encoding="utf-8"))
                    folder = response_file.stem.replace("response_", "")
                    files_index = data.get("files_index", {})
                    
                    ai_logger.debug(f"[TOOL:get_indexed_files] Repository '{folder}': {len(files_index)} files")
                    
                    result.append(f"\n📁 Repository: {folder}")
                    result.append(f"   Files indexed: {len(files_index)}")
                    
                    for file_path in list(files_index.keys())[:10]:
                        result.append(f"   - {file_path}")
                    
                    if len(files_index) > 10:
                        result.append(f"   ... and {len(files_index) - 10} more files")
                        
                except Exception as e:
                    ai_logger.warning(f"[TOOL:get_indexed_files] Failed to parse response file {response_file}: {str(e)}")
                    continue
        else:
            ai_logger.debug(f"[TOOL:get_indexed_files] LLM response directory not found")
        
        ai_logger.debug(f"[TOOL:get_indexed_files] Returning results")
        return "\n".join(result)
        
    except Exception as e:
        ai_logger.error(f"[TOOL:get_indexed_files] Error getting indexed files: {str(e)}", exc_info=True)
        return f"Error getting indexed files: {str(e)}"


# --- Code Proposal Tool (for Diff Viewer) ---

# In-memory storage for pending proposals (session_id -> proposal)
_pending_proposals: Dict[str, Dict[str, Any]] = {}


def propose_code_change(
    file_path: str, 
    search_block: str, 
    replacement_block: str,
    user_id: str = "918262"
) -> Dict[str, Any]:
    """
    Propose a code change without writing to disk.
    
    Use this tool when you want to modify a file. Instead of writing directly,
    this tool creates a proposal that the user can review and accept/reject.
    
    The tool finds the `search_block` in the file and replaces it with `replacement_block`.
    This is token-efficient - you only need to provide the changed portion.
    
    Args:
        file_path: Path to the file to modify (relative or absolute)
        search_block: The exact code block to find and replace. 
                      Must match the file content exactly (including whitespace).
        replacement_block: The new code to replace the search_block with.
        user_id: User ID for locating stored repositories.
        
    Returns:
        A dict with proposal details (for SSE propagation) including:
        - file_path: The target file
        - original_content: Full original file content
        - proposed_content: Full file content after replacement
        - success: Whether the search block was found
    """
    ai_logger.debug(f"[TOOL:propose_code_change] Called for file: {file_path}")
    ai_logger.debug(f"[TOOL:propose_code_change] Search block length: {len(search_block)} chars")
    ai_logger.debug(f"[TOOL:propose_code_change] Replacement block length: {len(replacement_block)} chars")
    
    try:
        # Find the file (similar logic to retrieve_code_file)
        path = Path(file_path)
        original_content = None
        resolved_path = None
        
        # Try direct path first
        if path.exists() and path.is_file():
            resolved_path = path
            original_content = path.read_text(encoding="utf-8", errors="replace")
            ai_logger.debug(f"[TOOL:propose_code_change] Found file at direct path: {path}")
        else:
            # Search in repo storage
            repo_storage = Path(REPO_STORAGE) / str(user_id)
            if repo_storage.exists():
                for repo_dir in repo_storage.iterdir():
                    if repo_dir.is_dir() and repo_dir.name not in ["chunks", "indexed_file", "llm_response"]:
                        potential_path = repo_dir / file_path
                        if potential_path.exists():
                            resolved_path = potential_path
                            original_content = potential_path.read_text(encoding="utf-8", errors="replace")
                            ai_logger.debug(f"[TOOL:propose_code_change] Found file at: {potential_path}")
                            break
        
        if original_content is None:
            ai_logger.warning(f"[TOOL:propose_code_change] File not found: {file_path}")
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path
            }
        
        # Check if search_block exists in the file
        if search_block not in original_content:
            ai_logger.warning(f"[TOOL:propose_code_change] Search block not found in file")
            return {
                "success": False,
                "error": "The search_block was not found in the file. Ensure it matches exactly (including whitespace).",
                "file_path": file_path
            }
        
        # Apply the replacement (in memory only!)
        proposed_content = original_content.replace(search_block, replacement_block, 1)
        ai_logger.debug(f"[TOOL:propose_code_change] Replacement applied in memory")
        
        # Store proposal for potential acceptance later
        proposal_id = f"{user_id}_{uuid.uuid4().hex}"
        _pending_proposals[proposal_id] = {
            "file_path": str(resolved_path),
            "original_content": original_content,
            "proposed_content": proposed_content,
            "search_block": search_block,
            "replacement_block": replacement_block
        }
        ai_logger.debug(f"[TOOL:propose_code_change] Stored proposal with ID: {proposal_id}")
        
        # Return structured data (this will be captured by EventCapture and sent to frontend)
        return {
            "success": True,
            "proposal_id": proposal_id,
            "file_path": file_path,
            "original_content": original_content,
            "proposed_content": proposed_content,
            "message": f"Proposed changes for {file_path}. Review the diff and accept or reject."
        }
        
    except Exception as e:
        ai_logger.error(f"[TOOL:propose_code_change] Error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }


def get_pending_proposal(proposal_id: str) -> Optional[Dict[str, Any]]:
    """Get a pending proposal by ID (for acceptance/rejection)."""
    return _pending_proposals.get(proposal_id)


def clear_proposal(proposal_id: str) -> bool:
    """Clear a proposal after acceptance or rejection."""
    if proposal_id in _pending_proposals:
        del _pending_proposals[proposal_id]
        return True
    return False

