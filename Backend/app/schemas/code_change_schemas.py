"""
Code Change Schemas for Structured Feature Generation Output

These schemas define the format for code changes that the Feature Generation
agent produces. Similar to GitHub's unified diff format with file paths and line numbers.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class CodeHunk(BaseModel):
    """A single block of code changes within a file."""
    start_line: int = Field(..., description="Starting line number in the original file")
    end_line: int = Field(..., description="Ending line number in the original file")
    original: str = Field(default="", description="Original code block (empty for new files)")
    modified: str = Field(..., description="Modified/new code block")
    diff: str = Field(default="", description="Unified diff format (@@ -x,y +x,y @@)")


class FileChange(BaseModel):
    """Changes to a single file."""
    file_path: str = Field(..., description="Relative path to the file")
    action: Literal["modify", "create", "delete"] = Field(..., description="Type of change")
    description: str = Field(..., description="Brief description of what this change does")
    hunks: List[CodeHunk] = Field(default_factory=list, description="List of code change blocks")
    full_content: Optional[str] = Field(None, description="Full file content (for new files)")


class CodeChangeResponse(BaseModel):
    """Complete response from Feature Generation agent with structured changes."""
    summary: str = Field(..., description="High-level summary of all changes")
    changes: List[FileChange] = Field(default_factory=list, description="List of file changes")
    dependencies: List[str] = Field(default_factory=list, description="New packages/dependencies required")
    notes: List[str] = Field(default_factory=list, description="Important implementation notes")
    breaking_changes: List[str] = Field(default_factory=list, description="Any breaking changes introduced")


class AnsweringResponse(BaseModel):
    """Response from Answering agent (no structured changes)."""
    answer: str = Field(..., description="The explanation/answer text")
    references: List[str] = Field(default_factory=list, description="File paths referenced")
    

class ChatAgentResponse(BaseModel):
    """
    Unified response format that can contain either:
    - A simple answer (from answering_agent)
    - Structured code changes (from feature_generation_agent)
    """
    response_type: Literal["answer", "code_change"] = Field(..., description="Type of response")
    
    # For answers (Q&A)
    answer: Optional[str] = Field(None, description="Text answer for questions")
    
    # For code changes (feature generation)
    code_changes: Optional[CodeChangeResponse] = Field(None, description="Structured code changes")
    
    # Common metadata
    agents_used: List[str] = Field(default_factory=list, description="Agents that contributed")
    execution_time_ms: Optional[int] = Field(None, description="Total processing time")
