from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker
from ai_code_review_assistant_backend.config import settings

# 1.create the engine connected to postegreSQL
engine=create_engine(
  settings.DATABASE_URL,
  echo=False # Change to True if you want to see raw SQL logs in the terminal
)

# 2. Session Factory
SessionLocal=sessionmaker(
  autocommit=False,
  autoflush=False,
  bind=engine
)

# 3.Base class for our future tables/models
Base=declarative_base()


# 4.To get DB sessions
def get_db():
  db=SessionLocal()
  try:
    yield db
  finally:
    db.close()   

