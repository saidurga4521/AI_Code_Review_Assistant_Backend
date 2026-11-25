from typing import List
from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session

from ai_code_review_assistant_backend.db.models import Repository,IndexedChunk
from ai_code_review_assistant_backend.db.session import get_db
from ai_code_review_assistant_backend.schemas.repository import RepositoryResponse,RepositoryCreate,ChunkResponse 
from ai_code_review_assistant_backend.services.indexing_service import index_repository_files

from ai_code_review_assistant_backend.schemas.rag import QuestionRequest,QuestionResponse
from ai_code_review_assistant_backend.services.rag_service import answer_codebase_question
from ai_code_review_assistant_backend.api.v1.auth import get_current_user
from ai_code_review_assistant_backend.db.models import User


# create the router
router=APIRouter(prefix='/repositories',tags=['Repositories'])

#1.connect a new repository
@router.post('/',response_model=RepositoryResponse)
def create_repository(repo_in:RepositoryCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
  """
  connect a new github repository to the assistant
  """
  existing_repo=db.query(Repository).filter(Repository.name == repo_in.name).first()

  if existing_repo:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=f"Repository with name {repo_in.name} already exists"
    )
  new_repo=Repository(
    name=repo_in.name,
    user_id=current_user.id,
    clone_url=repo_in.clone_url,
    default_branch=repo_in.default_branch,
    status="UNINDEXED"
  )

  db.add(new_repo)
  db.commit()
  db.refresh(new_repo) # Reads the row back, so new_repo.id and created_at are filled in
  return new_repo


#2.GET/repositories:List all repositories
@router.get('/',response_model=List[RepositoryResponse])
def list_all_repositories(db:Session=Depends(get_db),curr_user:User=Depends(get_current_user)):
  """
  Get All Connected Repositories owned by the current user(super users see all)
  """
  if curr_user.is_superuser:
    return db.query(Repository).all()
  #otherwise return repos owned by that user
  return db.query(Repository).filter((Repository.user_id == curr_user.id) | (Repository.user_id.is_(None))).all()

#3.GET/repositories/{repo_id}:Get single repository using id
@router.get('/{repo_id}',response_model=RepositoryResponse)
def get_repository(repo_id:int,db:Session=Depends(get_db),curr_user:User=Depends(get_current_user)):
  """
  Get the repository using repo_id
  """
  repo=db.query(Repository).filter(Repository.id == repo_id).first()
  if not repo:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=f"Repository with id {repo_id} not found"
    )

  #permission check
  if repo.user_id and repo.user_id != curr_user.id and not curr_user.is_superuser:
    raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this repository."
        )
  return repo

#4.POST/repositories/{repo_id}/index: Trigger indexing
@router.post('/{repo_id}/index')
def trigger_indexing(repo_id:int,repo_path:str,db:Session=Depends(get_db)):
  """
  Trigger code indexing for repository folder and store chunks in postgreSQL
  """

  repo=db.query(Repository).filter(Repository.id == repo_id).first()
  if not repo:
    raise HTTPException(status_code=404, detail="Repository not found.")

  try:
    chunks_count=index_repository_files(repo_id=repo.id,repo_path=repo_path,db=db)
    return {
      'message':f'Successfully indexed repository {repo.name}',
      'chunks_saved':chunks_count,
      'status':repo.status
    }

  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Indexing failed {str(e)}"
    )

#5.GET/repositories/{repo_id}/chunks:View all chunks for a repo
@router.get('/{repo_id}/chunks',response_model=List[ChunkResponse])
def get_repository_chunk(repo_id:int,db:Session=Depends(get_db)):
  """
  Get all the chunks extracted from this repository
  """
  chunks=db.query(IndexedChunk).filter(IndexedChunk.repo_id == repo_id).all()
  return chunks  


#6.Post/repositories/{repo_id}/ask
@router.post('/{repo_id}/ask',response_model=QuestionResponse)
def ask_codebase_question(repo_id:int,request:QuestionRequest,db:Session=Depends(get_db)):
  """
  Ask any technical question about a repository.
  Returns an answer strictly grounded in the codebase with file/line evidence
  """
  repo=db.query(Repository).filter(Repository.id == repo_id).first()
  if not repo:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Repository with ID {repo_id} not found"
    )

  try:
    result=answer_codebase_question(query=request.query,repo_id=repo_id,db=db)
    return result
  except Exception as e:
       raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating answer: {str(e)}"
        )

  