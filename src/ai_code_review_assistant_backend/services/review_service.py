import re
import json

from typing import Dict,List,Any,Optional
from sqlalchemy.orm import Session
from langchain_core.messages import SystemMessage,HumanMessage

from ai_code_review_assistant_backend.db.models import Repository,PRReview,ReviewFinding,WriteAction
from ai_code_review_assistant_backend.services.vector_store import search_codebase
from ai_code_review_assistant_backend.services.rag_service import get_llm

def review_pull_request(repo_id:int,diff_text:str,db:Session,pr_number:Optional[int]=None,commit_sha:Optional[str]=None)->Dict[str,Any]:
  """
  Direct ,clean PR Review Service:
  Reviews a git diff aganist the codebase and saved those finding into PostgreSQL
  """

  # check whether repo is existing or not 
  repo=db.query(Repository).filter(Repository.id == repo_id).first()
  if not repo:
    raise ValueError(
      f"Repository with the id {repo_id} not found"
    )

  # 1.RETRIVE releated codebase context from Postegresql using vector serach
  search_keywords=" ".join([line.lstrip('+-') for line in diff_text.splitlines() if line.startswith(('+','-'))][:5])
  related_chunks=search_codebase(query=search_keywords or 'core_logic',repo_id=repo_id,db=db,top_k=3)

  code_context="\n\n".join(f"File: {c['file_path']} (Lines {c['start_line']}-{c['end_line']}):\n{c['content']}" for c in related_chunks)

   # 2. Strict Prompt instructing Gemini to return JSON
  system_instruction = (
        "You are an expert Senior Code Reviewer & Security Auditor.\n"
        "Your job is to analyze the provided Git Diff and flag potential issues.\n\n"
        "You must evaluate 4 dimensions:\n"
        "1. BUG_RISK: Null pointer dereferences, logic errors, unhandled exceptions.\n"
        "2. SECURITY: SQL injection, hardcoded secrets/keys, path traversal, unsafe calls.\n"
        "3. MISSING_TESTS: Newly added logic or branches that lack unit test coverage.\n"
        "4. ARCHITECTURE: Breaking changes or API inconsistencies.\n\n"
        "OUTPUT FORMAT:\n"
        "You must respond ONLY with a valid JSON object matching this exact schema (no markdown, no backticks):\n"
        "{\n"
        '  "summary": "High-level summary of the PR and overall impact",\n'
        '  "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",\n'
        '  "findings": [\n'
        "    {\n"
        '      "file_path": "path/to/file.py",\n'
        '      "line_number": 42,\n'
        '      "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO",\n'
        '      "category": "BUG_RISK" | "SECURITY" | "MISSING_TESTS" | "ARCHITECTURE",\n'
        '      "title": "Short title of the issue",\n'
        '      "description": "Clear explanation of why this is a risk",\n'
        '      "suggested_diff": "Exact code fix diff (before/after) or null",\n'
        '      "evidence_snippet": "The problematic code line(s)"\n'
        "    }\n"
        "  ]\n"
        "}"
    )

  user_prompt = (
        f"<related_codebase_context>\n{code_context}\n</related_codebase_context>\n\n"
        f"<git_diff_to_review>\n{diff_text}\n</git_diff_to_review>\n\n"
        f"Perform the code review now and return ONLY the JSON object."
    )
  
  #3.call gemini
  llm=get_llm()
  response=llm.invoke([
     SystemMessage(content=system_instruction),
     HumanMessage(content=user_prompt)
  ])

  # Extract raw text
  raw_text=response.content
  if isinstance(raw_text,list):
    raw_text=''.join([p.get('text') for p in raw_text if isinstance(p,dict)])

  # clean any accidental markdown backticks
  clean_json_str=re.sub(r"^```json\s*","",raw_text.strip(),flags=re.MULTILINE) # re.MULTILINE means makes ^ on every line not only start of the whole
  clean_json_str=re.sub(r'^```\s*',"",clean_json_str,flags=re.MULTILINE).strip()

  review_data=json.loads(clean_json_str)

  # 4.Save to PostgreSQL ,create PRReview Record
  pr_review=PRReview(
    repo_id=repo_id,
    pr_number=pr_number,
    commit_hash=commit_sha,
    summary=review_data.get('summary','code review completed'),
    risk_level=review_data.get('risk_level','LOW')
  )

  db.add(pr_review)
  db.commit()
  db.refresh(pr_review)

  # 5.Save ReviewFindings and stage WriteActions in PostgreSQL
  saved_findings=[]
  for item in review_data.get('findings',[]):
    finding=ReviewFinding(
      review_id=pr_review.id,
      file_path=item.get('file_path','unknown'),
      line_number=item.get('line_number',1),
      severity=item.get('severity','MEDIUM'),
      category=item.get('category','BUG_RISK'),
      title=item.get('title','IssueDetected'),
      description=item.get("description", ""),
      suggested_diff=item.get("suggested_diff"),
      evidence_snippet=item.get("evidence_snippet") 
    )

    db.add(finding)
    db.commit()
    db.refresh(finding)
    saved_findings.append(finding)


    # stage a write action if there is any suggested fix
    if item.get('suggested_diff'):
      action=WriteAction(
        finding_id=finding.id,
        action_type='APPLY_PATCH',
        payload=item['suggested_diff'],
        status='PENDING_APPROVAL'
      )
      db.add(action)

  db.commit()  

  return {
        "review_id": pr_review.id,
        "summary": pr_review.summary,
        "risk_level": pr_review.risk_level,
        "findings_count": len(saved_findings),
        "findings": [
            {
                "id": f.id,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "severity": f.severity,
                "category": f.category,
                "title": f.title,
                "description": f.description,
                "suggested_diff": f.suggested_diff
            }
            for f in saved_findings
        ]
    }
      





