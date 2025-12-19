from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.init_db import create_tables, seed_problems_from_json
from app.api.deps import get_db, get_current_user
from app.db.models import User, Submission
from app.core.security import create_access_token, hash_password

from app.api.routers import auth, problems, submissions, profile, agents
from app.services.problems_service import list_problems, get_problem
from app.services.submissions_service import create_submission
from app.services.events_service import log_event

from app.agents.code_reviewer import CodeReviewerAgent
from app.agents.algorithm_mentor import AlgorithmMentorAgent
from app.agents.llm import DummyLLMClient, OpenAICompatibleClient
from app.core.config import settings


app = FastAPI(title="Gent System (Progress Navigator + Code Reviewer + Mentor)")

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
templates = Jinja2Templates(directory="app/web/templates")

app.include_router(auth.router)
app.include_router(problems.router)
app.include_router(submissions.router)
app.include_router(profile.router)
app.include_router(agents.router)


def get_llm_client():
    if settings.llm_api_key.strip():
        return OpenAICompatibleClient(settings.llm_base_url, settings.llm_api_key, settings.llm_model)
    return DummyLLMClient()


@app.on_event("startup")
def on_startup():
    create_tables()
    seed_problems_from_json()


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
def register_web(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if db.scalar(select(User).where(User.username == username)):
        return templates.TemplateResponse("register.html", {"request": request, "error": "username busy"})

    user = User(email=email, username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(sub=str(user.id))
    resp = RedirectResponse(url="/", status_code=302)
    resp.set_cookie("access_token", token, httponly=True, samesite="lax")
    return resp


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    probs = list_problems(db)
    total_attempts = len(user.submissions)
    total_solved = sum(1 for s in user.submissions if s.status == "accepted")

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "username": user.username,
            "total_attempts": total_attempts,
            "total_solved": total_solved,
            "problems": probs,
        },
    )


@app.get("/problem/{problem_id}", response_class=HTMLResponse)
def problem_page(problem_id: str, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    p = get_problem(db, problem_id)
    if not p:
        return RedirectResponse(url="/", status_code=302)
    log_event(db, user.id, "problem_view", {"problem_id": problem_id})
    return templates.TemplateResponse("problem.html", {"request": request, "problem": p, "review": None, "mentor": None})


@app.get("/mentor/{problem_id}", response_class=HTMLResponse)
def mentor_page(problem_id: str, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    p = get_problem(db, problem_id)
    if not p:
        return RedirectResponse(url="/", status_code=302)

    log_event(db, user.id, "mentor_requested", {"problem_id": problem_id})
    agent = AlgorithmMentorAgent(get_llm_client())
    res = agent.run(problem_statement=p.statement, examples=p.examples)

    return templates.TemplateResponse(
        "problem.html",
        {"request": request, "problem": p, "review": None, "mentor": res.payload["hints_text"]},
    )


@app.post("/problem/{problem_id}/submit", response_class=HTMLResponse)
def submit_problem(
    problem_id: str,
    request: Request,
    code: str = Form(...),
    language: str = Form("python"),
    time_spent_sec: int = Form(0),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    p = get_problem(db, problem_id)
    if not p:
        return RedirectResponse(url="/", status_code=302)

    sub = create_submission(db, user.id, problem_id, language, code, time_spent_sec)
    log_event(db, user.id, "submission_created", {"problem_id": problem_id, "submission_id": sub.id})

    # автозапуск code review
    log_event(db, user.id, "review_requested", {"submission_id": sub.id})
    reviewer = CodeReviewerAgent(get_llm_client())
    review_res = reviewer.run(db=db, submission=sub, problem_statement=p.statement)

    return templates.TemplateResponse(
        "problem.html",
        {"request": request, "problem": p, "review": review_res.payload["details"], "mentor": None},
    )


@app.get("/navigator", response_class=HTMLResponse)
def navigator_page(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # простой вывод в HTML без отдельного шаблона (по-студенчески)
    # можно быстро вынести в templates при желании
    return RedirectResponse(url="/api/agents/navigator", status_code=302)
