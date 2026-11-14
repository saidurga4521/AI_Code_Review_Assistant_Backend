## This file created just for temporary to test whether out table is creating on postgresql
from ai_code_review_assistant_backend.db.session import engine,Base
from ai_code_review_assistant_backend.db.models import Repository

print('connecting to PostgreSQL and creating tables')

Base.metadata.create_all(bind=engine)

print('sucessfull')