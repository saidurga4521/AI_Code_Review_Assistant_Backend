from ai_code_review_assistant_backend.db.session import SessionLocal
from ai_code_review_assistant_backend.services.rag_service import answer_codebase_question

db = SessionLocal()

try:
    question = "Explain how our database session is created and where the database URL comes from."
    print(f"--- Asking Gemini: '{question}' ---\n")

    result = answer_codebase_question(query=question, repo_id=1, db=db)

    print("🤖 AI ANSWER:")
    print(result["answer"])

    print("\n📎 VERIFIABLE EVIDENCE (Citations):")
    for ev in result["evidence"]:
        print(f"- {ev['file_path']} (Lines {ev['start_line']}-{ev['end_line']})")

finally:
    db.close()