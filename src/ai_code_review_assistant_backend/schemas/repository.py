import datetime
from pydantic import BaseModel,Field
from typing import Optional,List

#1.Schema for creating a new repository(RequestBody)
class RepositoryCreate(BaseModel):
  name:str=Field(...,example='my-org/my-project',description='Repository name')
  clone_url:Optional[str]=Field(None,example="https://github.com/my-org/my-project.git")
  default_branch:str=Field(default='main',example='main')

#2.schema for returning repository details (Response Body)

class RepositoryResponse(BaseModel):
  id:int
  user_id:Optional[int] =None #owner user id
  name:str
  clone_url:Optional[str] = None
  default_branch:str
  status:str
  created_at:datetime.datetime

  class Config:
    from_attributes=True # Allows Pydantic to read directly from SQLAlchemy models

#3.Schema for viewing on indexed chunk
class ChunkResponse(BaseModel):
  id: int
  file_path: str
  start_line: int
  end_line: int
  symbol_name: Optional[str] = None
  language: str
  content: str
  class Config:
      from_attributes = True