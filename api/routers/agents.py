from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.schemas.agents import ReviewOut, MentorHintOut, NavigatorOut
from app.services.problems_service import get_problem
from app.services.events_service import log_event
from app.db.models import Submission

from app.agents.code_reviewer import CodeReviewerAgent
from app.agents.algorithm_mentor import AlgorithmMentorAgent
from app.agents.progress_navigator import ProgressNavigatorAgent
from app.agents.llm import DummyLLMClient, OpenAICompatibleClient
from app.core.config import settings

router = APIRouter(prefix="/api/agents", tags=["agents"])


def get_llm_client():
    if settings.llm_api_key.strip():
        return OpenAICompatibleClient(settings.llm_base_url, settings.llm_api_key, settings.llm_model)
    return DummyLLMClient()


@router.post("/code_review/{submission_id}", response_model=ReviewOut)
def run_code_review(submission_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    submission = db.scalar(select(Submission).where(Submission.id == submission_id, Submission.user_id == user.id))
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    p = get_problem(db, submission.problem_id)
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")

    log_event(db, user.id, "review_requested", {"submission_id": submission_id})

    agent = CodeReviewerAgent(get_llm_client())
    res = agent.run(db=db, submission=submission, problem_statement=p.statement)
    return res.payload


@router.get("/mentor/{problem_id}", response_model=MentorHintOut)
def mentor(problem_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    p = get_problem(db, problem_id)
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")

    log_event(db, user.id, "mentor_requested", {"problem_id": problem_id})

    agent = AlgorithmMentorAgent(get_llm_client())
    res = agent.run(problem_statement=p.statement, examples=p.examples)
    return {"hints": [], "explanation": res.payload["hints_text"]}


@router.get("/navigator", response_model=NavigatorOut)
def navigator(db: Session = Depends(get_db), user=Depends(get_current_user)):
    agent = ProgressNavigatorAgent(get_llm_client())
    res = agent.run(db=db, user_id=user.id)
    return {"recommendations": [res.payload["recommendations_text"]], "weak_topics": res.payload["weak_topics"]}
