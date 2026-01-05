from pydantic import BaseModel, Field
from typing_extensions import List

class ParseGithubUrl(BaseModel):
    github_repo: str