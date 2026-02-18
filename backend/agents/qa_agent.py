"""QA Agent — Test cases from user stories."""

import json

from agents.state import PipelineState
from services.llm_service import call_llm_json
from services.db_service import save_artifact, log_decision

SYSTEM_PROMPT = """You are a QA Engineer agent in a software development pipeline.
Your job is to generate test cases from user stories.

RULES:
- Generate test cases for EACH user story provided.
- Each test case must reference its parent user story IDs and requirement IDs.
- Include both positive and negative test cases.
- Use the DADO/CUANDO/ENTONCES (Given/When/Then) format for steps.
- IDs must follow the format TC-001, TC-002, etc.
- Respond ONLY with valid JSON, no extra text."""

USER_PROMPT_TEMPLATE = """Given the following user stories, generate comprehensive test cases.

## User Stories
{user_stories}

## Requirements (for traceability)
{requirements}

Respond with this exact JSON structure:
{{
  "artifacts": [
    {{
      "id": "TC-001",
      "title": "Descriptive test case title",
      "user_story_ids": ["US-001"],
      "requirement_ids": ["REQ-001"],
      "preconditions": ["User is logged in", "..."],
      "steps": ["DADO que ...", "CUANDO ...", "ENTONCES ..."],
      "expected_result": "Clear expected outcome",
      "type": "positive"
    }}
  ]
}}

Generate at least 2 test cases per user story (1 positive, 1 negative). Respond ONLY with JSON."""


async def run_qa_agent(state: PipelineState) -> dict:
    """Receive user stories + requirements and generate test cases."""
    run_id = state["run_id"]
    user_stories = state.get("user_stories") or {}
    requirements = state.get("requirements") or {}

    await log_decision(run_id, "qa_agent", "started", {
        "input_stories": len(user_stories.get("artifacts", [])),
    })

    prompt = USER_PROMPT_TEMPLATE.format(
        user_stories=json.dumps(user_stories, indent=2, ensure_ascii=False),
        requirements=json.dumps(requirements, indent=2, ensure_ascii=False),
    )

    result = await call_llm_json(prompt, SYSTEM_PROMPT)

    # Save each test case as an artifact
    for tc in result.get("artifacts", []):
        parent_ids = tc.get("user_story_ids", []) + tc.get("requirement_ids", [])
        await save_artifact(
            run_id=run_id,
            artifact_id=tc["id"],
            agent="qa_agent",
            artifact_type="test_case",
            content=tc,
            parent_ids=parent_ids,
        )

    await log_decision(run_id, "qa_agent", "completed", {
        "test_cases_generated": len(result.get("artifacts", [])),
    })

    return {"test_cases": result}
