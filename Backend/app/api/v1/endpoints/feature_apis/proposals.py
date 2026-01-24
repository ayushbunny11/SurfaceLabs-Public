"""
Proposal Management API
Single endpoint for handling code proposal actions.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Literal

from app.services.proposals.proposal_service import handle_proposal_action, ProposalError


router = APIRouter()


class ProposalActionRequest(BaseModel):
    proposal_id: str
    action: Literal["accept", "reject"]


class ProposalActionResponse(BaseModel):
    success: bool
    action: str
    message: str
    file_path: str | None = None


@router.post("/action", response_model=ProposalActionResponse)
async def proposal_action(request: ProposalActionRequest):
    """
    Handle a code proposal action (accept or reject).
    
    - **accept**: Writes the proposed changes to the target file.
    - **reject**: Clears the proposal from memory without applying.
    """
    try:
        result = handle_proposal_action(
            proposal_id=request.proposal_id,
            action=request.action
        )
        return ProposalActionResponse(**result)
        
    except ProposalError as e:
        if e.code == "NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
        elif e.code == "FILE_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
        elif e.code == "INVALID_DATA":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)
