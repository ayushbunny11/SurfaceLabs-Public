from pydantic import BaseModel, Field
from typing_extensions import List, Dict, Optional
from datetime import datetime

class ParseGithubUrl(BaseModel):
    github_repo: str
    
class AnalysisRequest(BaseModel):
    folder_ids: List[str] = Field(..., description="List of folder IDs to analyze")
    
class FileInfo(BaseModel):
    path: str
    relative_path: str
    size: int
    lines_of_code: int
    extension: str
    language: str
    hash: str


class FileChunk(BaseModel):
    """Group of related files for analysis"""
    chunk_id: str
    directory: str
    files: List[FileInfo]
    token_estimate: int


class ChunkSummary(BaseModel):
    """AI analysis result for a chunk"""
    chunk_id: str
    directory: str
    purpose: str
    key_files: List[Dict[str, str]]  # [{file: purpose}, ...]
    dependencies: List[str]
    patterns: List[str]


class ProjectOverview(BaseModel):
    """Final synthesized project understanding"""
    project_name: str
    tech_stack: List[str]
    architecture: str
    main_components: Dict[str, str]
    data_flow: str
    conventions: Dict[str, str]
    overview: str
    # Metadata
    total_files: int
    total_lines: int
    languages: Dict[str, int]
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query text")


class SearchResultItem(BaseModel):
    chunk_id: str
    score: float
    content: dict
    relevance: str  # "high", "medium", "low"


class SearchResponse(BaseModel):
    status: str
    message: str
    data: List[SearchResultItem]
    total_results: int
    query: str