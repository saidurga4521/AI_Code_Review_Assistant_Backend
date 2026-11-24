import datetime
from sqlalchemy import Column,Integer,String,DateTime,ForeignKey,Text,Boolean
from sqlalchemy.orm import relationship
from ai_code_review_assistant_backend.db.session import Base

class Repository(Base):
  __tablename__= "repositories"

  id=Column(Integer,primary_key=True,index=True)
  user_id=Column(Integer,ForeignKey('users.id'),nullable=True)
  name=Column(String(255),unique=True,index=True,nullable=False)
  clone_url=Column(String(512),nullable=True)
  default_branch=Column(String(100),default='main')
  status=Column(String(50),default='UNINDEXED') # UNINDEXED, INDEXING, READY, FAILED
  created_at =Column(DateTime,default=datetime.datetime.now)

  # Link back to user
  owner=relationship('User',back_populates='repositories')

  ## Relationship to its chunks
  chunks=relationship('IndexedChunk',back_populates='repository')
  reviews=relationship('PRReview',back_populates='repository')


class IndexedChunk(Base):
  __tablename__='indexed_chunk'

  id=Column(Integer,primary_key=True,nullable=False)
  repo_id=Column(Integer,ForeignKey('repositories.id'),nullable=False)
  file_path=Column(String(512),nullable=False,index=True)
  start_line=Column(Integer,nullable=False)
  end_line=Column(Integer,nullable=False)
  symbol_name=Column(String(512),nullable=True)
  language=Column(String(100),default='plaintext')
  content=Column(Text,nullable=False)
  embedding_json=Column(Text,nullable=True)

  # Link back to repository table
  repository = relationship('Repository',back_populates='chunks')


class PRReview(Base):

  __tablename__='pr_review'

  id=Column(Integer,primary_key=True,index=True)
  repo_id=Column(Integer,ForeignKey('repositories.id'),nullable=False)
  pr_number=Column(Integer,nullable=True)
  commit_hash=Column(String(64),nullable=True)
  summary=Column(Text,nullable=True)
  risk_level=Column(String(50),default='LOW') #LOW,MEDIUM,HIGH,CRITICAL
  created_at=Column(DateTime,default=datetime.datetime.now)

  repository = relationship("Repository",back_populates='reviews')

  ## Relationship to findings
  findings=relationship('ReviewFinding',back_populates='review',cascade='all,delete-orphan')

  ## cascade='all, delete-orphan' means if a PR review is deleted, all its individual findings get cleaned up automatically

class ReviewFinding(Base):

  __tablename__ = 'review_findings'

  id=Column(Integer,primary_key=True,index=True)
  review_id=Column(Integer,ForeignKey('pr_review.id'),nullable=False)
  file_path=Column(String(512),nullable=False)
  line_number=Column(Integer,nullable=False)
  severity=Column(String(50),nullable=False) ## CRITICAL,HIGH,MEDIUM,LOW,INFO
  category=Column(String(50),nullable=False)
  title=Column(String(255),nullable=False)
  description=Column(Text,nullable=False)
  suggested_diff=Column(Text,nullable=True)
  evidence_snippet=Column(Text,nullable=True)

  # Link back to PRReview
  review=relationship('PRReview',back_populates='findings') 

  # Relation to actions
  actions=relationship('WriteAction',back_populates='finding',cascade='all,delete-orphan')

  # Relation to feedback
  feedback=relationship('DeveloperFeedback',back_populates='finding',cascade='all,delete-orphan')

class WriteAction(Base):
   __tablename__ = 'write_actions'

   id=Column(Integer,primary_key=True,index=True)
   finding_id=Column(Integer,ForeignKey('review_findings.id'),nullable=True)
   action_type=Column(String(50),nullable=False)
   payload=Column(Text,nullable=True)
   status=Column(String(50))
   resolved_by=Column(String(100),nullable=True)
   resolved_at=Column(DateTime,nullable=True)
   created_at=Column(DateTime,default=datetime.datetime.now)

   # Link back to ReviewFinding

   finding=relationship('ReviewFinding',back_populates='actions')

class DeveloperFeedback(Base):
   __tablename__ = 'developer_feedback'

   id=Column(Integer,primary_key=True,index=True)
   finding_id=Column(Integer,ForeignKey('review_findings.id'),nullable=False)
   is_useful=Column(Boolean,nullable=False)
   reason=Column(String(50),nullable=True)
   comment=Column(Text,nullable=True) 
   created_at=Column(DateTime,default=datetime.datetime.now) 

   # Link Back to Review Finding
   finding=relationship('ReviewFinding',back_populates='feedback')


class User(Base):
  __tablename__ = 'users'

  id=Column(Integer,primary_key=True,index=True,nullable=False)
  email=Column(String(255),unique=True,index=True,nullable=False)
  hashed_password=Column(String(255),nullable=False)
  full_name=Column(String(255),nullable=True)
  is_active=Column(Boolean,default=True)
  is_superuser=Column(Boolean,default=True)
  created_at=Column(DateTime,default=datetime.datetime.now)

  #Relationship to owned repositories
  repositories=relationship('Repository',back_populates='owner',cascade="all,delete-orphan")


   



  