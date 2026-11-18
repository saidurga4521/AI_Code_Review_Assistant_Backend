import numpy as np
from typing import Any,List,Dict
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from ai_code_review_assistant_backend.config import settings
from sentence_transformers import SentenceTransformer

import json
from sqlalchemy.orm import Session
from ai_code_review_assistant_backend.db.models import IndexedChunk


# 1. Load the SentanceTransformer model (cached locally after first download)
MODEL_NAME='all-MiniLM-L6-v2'
model=SentenceTransformer(MODEL_NAME)

def embed_documents(texts:List[str])->List[List[float]]:

  if not texts:
    return []
  embeddings=model.encode(texts,batch_size=32,convert_to_numpy=True) 
  return embeddings.tolist()

def embed_text(text:str)->List[float]:
  """
  Generate a embedding vector for a single query  or code string
  """
  embedding=model.encode(text,convert_to_numpy=True)
  return embedding.tolist()

def cosine_similarity(vec_a:List[float],vec_b:List[float])->float:
  """
  Compute cosine similarity between two embedding vectors.
  Returns a score between -1.0 and 1.0(higher = closer meaning).
  """

  #convert list in numpy arrays
  a=np.array(vec_a,dtype=np.float32)
  b=np.array(vec_b,dtype=np.float32)

  # finding the magnitude
  norm_a=np.linalg.norm(a)
  norm_b=np.linalg.norm(b)

  if norm_a ==0 or norm_b == 0:
    return 0.0
  
  return float(np.dot(a,b)/(norm_a*norm_b))


def save_chunk_embeddings(repo_id:int,db:Session)->int:
  """
  Find all the chunks in postgreSQL for this repo that dont have
  embeddings yet,
  generates their vectors in batches and saves them in postgreSQL
  """

  chunks=db.query(IndexedChunk).filter(
    IndexedChunk.repo_id == repo_id,
    IndexedChunk.embedding_json.is_(None)
    ).all()

  if not chunks:
    print("All chunks already have embeddings")
    return 0

  print(f"Generating Embeddings for {len(chunks)} chunks") 

  texts=[chunk.content for chunk in chunks]
  vectors=embed_documents(texts)

  for chunk,vector in zip(chunks,vectors):
    chunk.embedding_json=json.dumps(vector)

  db.commit()
  print(f"Successfully Saved embeddings for {len(chunks)} chunks in PostegreSQL")

  return len(chunks)


def search_codebase(query:str,repo_id:int,db:Session,top_k:int=5)->List[Dict[str,Any]]:
  """
  Semantic Search (RAG Retrieval):
  Takes a query,turns it into a vector,and finds the tok-K most
  relevant code chunks in PostgreSQL using Cosine Similarity
  """

  # 1.Turn your query into vector
  query_vector=embed_text(query)

  # 2.Fetch all chunks for this repository from PosgreSQL
  chunks=db.query(IndexedChunk).filter(
    IndexedChunk.repo_id==repo_id,
    IndexedChunk.embedding_json.isnot(None)
  ).all()

  if not chunks:
    return []

  # 3.calculate the similarity score for each chunk
  scored_chunks=[]
  for chunk in chunks:
    chunk_vector=json.loads(chunk.embedding_json)
    score=cosine_similarity(query_vector,chunk_vector)

    scored_chunks.append({
        "chunk_id": chunk.id,
        "file_path": chunk.file_path,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "symbol_name": chunk.symbol_name,
        "language": chunk.language,
        "content": chunk.content,
        "similarity_score": round(score, 4)
    })

  #4.sort by highest similarity score first(closest meaning)
  scored_chunks.sort(key=lambda x:x['similarity_score'],reverse=True)

  # Return top K marches
  return scored_chunks[:top_k]





   



