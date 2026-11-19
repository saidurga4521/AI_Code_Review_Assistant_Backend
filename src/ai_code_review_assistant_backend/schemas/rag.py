from typing import List
from pydantic import BaseModel,Field

#1.Request Body when developer asks

class QuestionRequest(BaseModel):
  query:str=Field(
    ...,
    example='How is database session created and where does the URL come from?',
    description='The question to ask about the codebase'
  )

#2.Citation evidence item
class EvidenceItem(BaseModel):
  file_path:str
  start_line:int
  end_line:int
  similarity_score:float

#3.Response Body from LLM answer + citations

class QuestionResponse(BaseModel):
  answer:str
  evidence:List[EvidenceItem]  

  
