from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_code_review_assistant_backend.db.session import Base,engine
from ai_code_review_assistant_backend.config import settings
from ai_code_review_assistant_backend.api.v1.repositories import router as repository_router 
from ai_code_review_assistant_backend.api.v1.reviews import router as review_router
from ai_code_review_assistant_backend.api.v1.action import router as actions_router
from ai_code_review_assistant_backend.api.v1.feedback import router as feedback_router


#1.make sure all the database tables exist otherwise its creates all the tables
Base.metadata.create_all(bind=engine)

#2.Intializes the FastAPI App
app=FastAPI(
  title=settings.PROJECT_NAME,
  version=settings.VERSION,
  description='Backend API for AI Code Review & Repository Assistant'
)

#3.Add CORS Middlware(allows requests from frontend dashboards)
app.add_middleware(CORSMiddleware,
  allow_origins=['*'], # Allows all origins in development
  allow_headers=['*'],
  allow_credentials=True, # Allow cookies and login headers to be sent
  allow_methods=['*']
)

#4.Include our Routers under /api/v1
app.include_router(repository_router,prefix=settings.API_V1_STR)
app.include_router(review_router,prefix=settings.API_V1_STR)
app.include_router(actions_router,prefix=settings.API_V1_STR)
app.include_router(feedback_router,prefix=settings.API_V1_STR)

#5.Health check endpoint
@app.get('/health',tags=['Health'])
def health_check():
  return {
    "status": "healthy",
    "project": settings.PROJECT_NAME,
    "version": settings.VERSION
  }


#run command for locally:
# uv run uvicorn ai_code_review_assistant_backend.main:app --reload