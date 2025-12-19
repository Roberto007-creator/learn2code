import ast
from sqlalchemy.orm import Session
from app.agents.base import BaseAgent, AgentResult
from app.agents.llm import LLMMessage
from app.agents.prompts import CODE_REVIEW_SYSTEM
from app.agents.parse import parse_scores
from app.db.models import CodeReview, Submission


def _basic_python_static_checks(code: str) -> dict:
    issues = []
    had_edge_case_issue = False

    if "print(" in code:
        issues.append("Есть print(): на платформах часто нужно вернуть значение, а не печатать.")
    if "input(" in code:
        issues.append("Есть input(): обычно решения должны быть функцией, без stdin (зависит от формата).")

    try:
        tree = ast.parse(code)
        max_loop_depth = 0

        def walk(node, depth=0):
            nonlocal max_loop_depth
            is_loop = isinstance(node, (ast.For, ast.While))
            new_depth = depth + (1 if is_loop else 0)
            if is_loop:
                max_loop_depth = max(max_loop_depth, new_depth)
            for child in ast.iter_child_nodes(node):
                walk(child, new_depth)

        walk(tree)

        if max_loop_depth >= 2:
            issues.append("Похоже на вложенные циклы: проверь сложность (возможно O(n^2)).")
            had_edge_case_issue = True

    except SyntaxError:
        issues.append("Код не парсится как Python (SyntaxError).")
        had_edge_case_issue = True

    return {"issues": issues, "had_edge_case_issue": had_edge_case_issue}


class CodeReviewerAgent(BaseAgent):
    name = "code_reviewer"

    def __init__(self, llm_client):
        self.llm = llm_client

    def run(self, db: Session, submission: Submission, problem_statement: str) -> AgentResult:
        checks = _basic_python_static_checks(submission.code)

        llm_text = self.llm.chat(
            [
                LLMMessage(role="system", content=CODE_REVIEW_SYSTEM),
                LLMMessage(
                    role="user",
                    content=(
                        f"Условие:\n{problem_statement}\n\n"
                        f"Язык: {submission.language}\n"
                        f"Код:\n{submission.code}\n\n"
                        f"Предварительные статические замечания: {checks['issues']}"
                    ),
                ),
            ]
        )

        scores = parse_scores(llm_text)
        if scores:
            score_readability, score_correctness, score_efficiency = scores
        else:
            score_readability, score_correctness, score_efficiency = 6, 6, 6
            if "SyntaxError" in llm_text:
                score_correctness = 2

        review = CodeReview(
            submission_id=submission.id,
            summary="Ревью готово",
            details=llm_text,
            score_readability=score_readability,
            score_correctness=score_correctness,
            score_efficiency=score_efficiency,
        )
        db.add(review)

        submission.had_edge_case_issue = checks["had_edge_case_issue"]
        submission.error_count = len(checks["issues"])

        db.commit()

        return AgentResult(
            ok=True,
            payload={
                "summary": review.summary,
                "details": review.details,
                "score_readability": review.score_readability,
                "score_correctness": review.score_correctness,
                "score_efficiency": review.score_efficiency,
            },
            debug={"static_issues": checks["issues"]},
        )
