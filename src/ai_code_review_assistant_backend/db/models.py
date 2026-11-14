import datetime
from sqlalchemy import Column,Integer,String,DateTime
from ai_code_review_assistant_backend.db.session import Base

class Repository(Base):
  __tablename__="repositories"

  id=Column(Integer,primary_key=True,index=True)
  name=Column(String(255),unique=True,index=True,nullable=False)
  clone_url=Column(String(512),nullable=True)
  default_branch=Column(String(100),default='main')
  status=Column(String(50),default='UNINDEXED') # UNINDEXED, INDEXING, READY, FAILED
  created_at =Column(DateTime,default=datetime.datetime.now)