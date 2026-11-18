import os
from pathlib import Path
from typing import List,Dict,Any
from sqlalchemy.orm import Session
from ai_code_review_assistant_backend.db.models import Repository,IndexedChunk

from langchain_text_splitters import Language,RecursiveCharacterTextSplitter
# Directories we should ALWAYS ignore
IGNORE_DIRS = {
    ".git", ".github", "__pycache__", "venv", ".venv", "env",
    "node_modules", "dist", "build", ".next", ".cache", "target"
}

# File extensions that are not human-readable source code
IGNORE_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".png", ".jpg", ".jpeg", ".gif", ".ico",
    ".svg", ".mp4", ".pdf", ".zip", ".tar", ".gz", ".lock", ".min.js"
}

# Map file extensions to LangChain's syntax-aware languages
EXTENSION_TO_LANGUAGE = {
    ".py": Language.PYTHON,
    ".js": Language.JS,
    ".jsx": Language.JS,
    ".ts": Language.TS,
    ".tsx": Language.TS,
    ".java": Language.JAVA,
    ".cpp": Language.CPP,
    ".c": Language.CPP,
    ".cs": Language.CSHARP,
    ".go": Language.GO,
    ".rs": Language.RUST,
    ".php": Language.PHP,
    ".rb": Language.RUBY,
    ".html": Language.HTML,
    ".md": Language.MARKDOWN,
}

def should_index_file(file_path:Path,max_size_kb:int = 500)->bool:
  """
   Decides whether a file should be indexed or skipped.
   Returns True if the file is safe to index,False otherwise
  """

  #1.skip any part of the path is in our ignore our ignore directories
  if any(part in IGNORE_DIRS  for part in file_path.parts):
    return False

  #2.skip if any extension in our ignore extensions
  if file_path.suffix.lower() in IGNORE_EXTENSIONS:
    return False

  #3.skip if the filepath is too large
  if file_path.is_file():
    try:
      file_size_kb=file_path.stat().st_size/1024
      if file_size_kb > max_size_kb:
        return False
    except OSError:
      return False

  return True  


# ## store the code in chunks
# def chunk_by_lines(file_path:str,code:str,chunk_size:int=40,overlap:int=5)->List[Dict[str,Any]]:

#   """
#   Universal chunker for ALL languages(Python,JS,Java,Go,etc..)
#   Slices code line by line with a small overlap so context isn't lost
#   """

#   lines=code.splitlines()
#   if not lines:
#     return []

#   chunks=[]
#   step=max(1,chunk_size-overlap)

#   for i in range(0,len(lines),step):
#     chunk_lines=lines[i:i+chunk_size]
#     start_line=i+1
#     end_line=i+len(chunk_lines)

#     chunks.append({
#       'file_path':file_path,
#       'start_line':start_line,
#       'end_line':end_line,
#       'symbol_name':f'lines_{start_line}_{end_line}',
#       'language':Path(file_path).suffix.lstrip('.') or 'plaintext',
#       'content':'\n'.join(chunk_lines)
#     })

#   return chunks


# def chunk_file(file_path:Path,chunk_size:int=40,overlap:int=5) ->List[Dict[str,Any]]:
#   """
#   Reads a file and returns its chunks
#   """
#   try:
#     with open(file_path,'r',encoding='utf8',errors='ignore') as f:
#       code=f.read()
#   except Exception as e:
#     print(f"Errro Reading {file_path}:{e}")
#     return []

#   return chunk_by_lines(str(file_path),code,chunk_size=chunk_size,overlap=overlap)


def chunk_file(file_path:Path,chunk_size:int =600,chunk_overlap:int=100)->List[Dict[str,Any]]:
  """
  Uses Langchain's Splitter to split files into chunks
  while keeping classes,functions, and methods together
  supports Python,Java,JS,TS,C++,Go,Rust and more.
  """

  # read the file
  try:
    with open(file_path,'r',encoding='utf-8',errors='ignore') as f:
      code=f.read()
  except Exception as e:
    print(f"Error reading {file_path}: {e}")
    return []

  if not code.strip():
    return []
  ext=file_path.suffix.lower()
  lang=EXTENSION_TO_LANGUAGE.get(ext)

  #1.choose the language aware splitter if supported,else general text splitter
  if lang:
    splitter=RecursiveCharacterTextSplitter.from_language(
      language=lang,
      chunk_size=chunk_size,
      chunk_overlap=chunk_overlap
    )
  else:
    splitter=RecursiveCharacterTextSplitter(
      chunk_size=chunk_size,
      chunk_overlap=chunk_overlap
    )

  # 2.split the code into chunks and it retuns in documents
  docs=splitter.create_documents([code])

  # 3.calculate exact line numbers for each chunk
  all_lines=code.splitlines()
  chunks=[]
  curr_search_idx=0

  for doc in docs:
    chunk_content=doc.page_content
    first_line=chunk_content.splitlines()[0] if chunk_content.splitlines() else ''

    #Locate where this chunk starts in the original file
    start_line=1
    for idx in range(curr_search_idx,len(all_lines)):
      if first_line and first_line.strip() in all_lines[idx]:
        start_line=idx+1
        curr_search_idx=idx
        break

    line_count=len(chunk_content.splitlines())
    end_line=start_line+max(1,line_count)-1

    chunks.append({
      'file_path':str(file_path),
      'start_line':start_line,
      'end_line':end_line,
      'symbol_name':f"{lang.value if lang else 'text'}_chunk_{start_line}_{end_line}",
      'language':lang.value if lang else ext.lstrip('.') or 'plaintext',
      'content':chunk_content
    }) 

  return chunks     



  


def index_repository_files(repo_id:int,repo_path:str,db:Session)->int:
  """
  crawls an entire repository directory,chunks all valid source files,
  and saves the chunks into the database
  Returns the total number of chunks created
  """

  repo=db.query(Repository).filter(Repository.id == repo_id).first()

  if not repo:
    raise ValueError(f"Repository with ID {repo_id} not found")

  #1.update the status to INDEXING
  repo.status ='INDEXING'
  db.commit()

  total_chunks_saved=0
  root_path=Path(repo_path)

  try:
    #2.walk through all files
    for file_path in root_path.rglob("*"): ##rglob:It is the crawler part. It walks through all folders and finds every file
      if not file_path.is_file():
        continue

      #check if this file should be indexed or not
      if not should_index_file(file_path):
        continue

      #calculate relative path
      relative_path=str(file_path.relative_to(root_path)) # This relative path just for storing

      #chunk the file
      chunks=chunk_file(file_path)

      #3.create a database records for each chunks
      for chunk_data in chunks:
        db_chunk=IndexedChunk(
          repo_id=repo.id,
          file_path=relative_path,
          start_line=chunk_data['start_line'],
          end_line=chunk_data['end_line'],
          symbol_name=chunk_data['symbol_name'],
          language=chunk_data['language'],
          content=chunk_data['content']
        )

        db.add(db_chunk)
        total_chunks_saved+=1

    #4.Mark Repository as READY
    repo.status='READY'
    db.commit()
    print(f"Successfully indexed repository {repo.name}")
    return total_chunks_saved       

  except Exception as e:
    repo.status='FAILED'
    db.commit()
    print(f"Failed to Index repository:{e}")



  

  