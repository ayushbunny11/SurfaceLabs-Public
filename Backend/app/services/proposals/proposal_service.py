"""
Proposal Management Service
Handles the core logic for accepting/rejecting code proposals.
"""
from pathlib import Path
from typing import Literal

from app.utils.logget_setup import app_logger
from app.services.agents.agent_tools import get_pending_proposal, clear_proposal


class ProposalError(Exception):
    """Custom exception for proposal-related errors."""
    def __init__(self, message: str, code: str = "PROPOSAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


def handle_proposal_action(
    proposal_id: str, 
    action: Literal["accept", "reject"]
) -> dict:
    """
    Handle a proposal action (accept or reject).
    
    Args:
        proposal_id: The unique identifier of the proposal.
        action: Either "accept" (writes to file) or "reject" (clears from memory).
    
    Returns:
        A dict with success status and message.
    
    Raises:
        ProposalError: If the proposal is not found or write fails.
    """
    app_logger.info(f"[PROPOSAL] Handling action '{action}' for proposal: {proposal_id}")
    
    # Get the proposal from in-memory storage
    proposal = get_pending_proposal(proposal_id)
    
    if not proposal:
        app_logger.warning(f"[PROPOSAL] Proposal not found: {proposal_id}")
        raise ProposalError(
            f"Proposal '{proposal_id}' not found or already processed.",
            code="NOT_FOUND"
        )
    
    file_path = proposal.get("file_path")
    
    # Handle reject action - just clear and return
    if action == "reject":
        clear_proposal(proposal_id)
        app_logger.info(f"[PROPOSAL] Rejected and cleared: {proposal_id}")
        return {
            "success": True,
            "action": "reject",
            "message": "Proposal rejected and cleared.",
            "file_path": file_path
        }
    
    # Handle accept action - write to file
    proposed_content = proposal.get("proposed_content")
    
    if not file_path or proposed_content is None:
        app_logger.error(f"[PROPOSAL] Invalid proposal data: {proposal_id}")
        raise ProposalError(
            "Invalid proposal data. Missing file_path or proposed_content.",
            code="INVALID_DATA"
        )
    
    try:
        target_path = Path(file_path)
        
        if not target_path.exists():
            app_logger.error(f"[PROPOSAL] Target file does not exist: {file_path}")
            raise ProposalError(f"Target file not found: {file_path}", code="FILE_NOT_FOUND")
        
        # Write the new content
        target_path.write_text(proposed_content, encoding="utf-8")
        app_logger.info(f"[PROPOSAL] Successfully applied changes to {file_path}")
        
        # Clear the proposal from storage
        clear_proposal(proposal_id)
        
        return {
            "success": True,
            "action": "accept",
            "message": f"Changes applied successfully to {target_path.name}",
            "file_path": str(file_path)
        }
        
    except ProposalError:
        raise
    except Exception as e:
        app_logger.exception(f"[PROPOSAL] Failed to write file: {e}")
        raise ProposalError(f"Failed to apply changes: {str(e)}", code="WRITE_ERROR")
