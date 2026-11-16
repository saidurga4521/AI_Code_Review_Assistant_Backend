from ai_code_review_assistant_backend.db.session import SessionLocal
from ai_code_review_assistant_backend.db.models import Repository, IndexedChunk
from ai_code_review_assistant_backend.services.indexing_service import index_repository_files

db = SessionLocal()

try:
    # 1. Create or get a test repository in the database
    repo = db.query(Repository).filter(Repository.name == "MCP").first()
    if not repo:
        repo = Repository(
            name="MCP",
            clone_url="https://github.com/saidurga4521/MCP.git",
            default_branch="main"
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        print(f"Created repository row with ID: {repo.id}")
    else:
        print(f"Found existing repository with ID: {repo.id}")

    # 2. Run our indexing engine on the 'src' folder
    print("Indexing the 'src' directory...")
    chunks_count = index_repository_files(repo_id=repo.id, repo_path="src", db=db)

    # 3. Verify chunks in PostgreSQL
    total_in_db = db.query(IndexedChunk).filter(IndexedChunk.repo_id == repo.id).count()
    print(f"\n🎉 SUCCESS! Repository status: '{repo.status}'")
    print(f"Total chunks indexed and stored in PostgreSQL: {total_in_db}")

finally:
    db.close()