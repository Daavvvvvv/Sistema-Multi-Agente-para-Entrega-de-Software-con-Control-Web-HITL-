"""Tests for Pydantic schema validation and artifact traceability.

These tests verify that the 7 artifact types conform to their schemas
and that the REQ → US → TC → Design traceability chain is intact.
"""

import pytest
from pydantic import ValidationError

from models.schemas import (
    Requirement,
    RequirementsOutput,
    InceptionOutput,
    MvpScope,
    Risk,
    UserStory,
    UserStoriesOutput,
    TestCase,
    TestCasesOutput,
    DiagramData,
    DiagramsOutput,
)
from conftest import (
    FAKE_REQUIREMENTS,
    FAKE_INCEPTION,
    FAKE_USER_STORIES,
    FAKE_TEST_CASES,
    FAKE_DIAGRAMS,
)


# ─── Requirement Schema ─────────────────────────────────────────────


class TestRequirementSchema:
    def test_valid_requirement(self):
        req = Requirement(**FAKE_REQUIREMENTS["artifacts"][0])
        assert req.id == "REQ-001"
        assert req.type in ("functional", "non_functional")
        assert req.priority in ("high", "medium", "low")

    def test_requirements_output(self):
        output = RequirementsOutput(**FAKE_REQUIREMENTS)
        assert len(output.artifacts) == 3
        assert output.domain_summary != ""
        assert len(output.assumptions) >= 1

    def test_requirement_ids_sequential(self):
        output = RequirementsOutput(**FAKE_REQUIREMENTS)
        ids = [a.id for a in output.artifacts]
        for i, art_id in enumerate(ids, start=1):
            assert art_id == f"REQ-{i:03d}"

    def test_requirement_missing_title_fails(self):
        with pytest.raises(ValidationError):
            Requirement(id="REQ-001", description="desc", type="functional", priority="high")

    def test_requirement_types_valid(self):
        output = RequirementsOutput(**FAKE_REQUIREMENTS)
        valid_types = {"functional", "non_functional"}
        for req in output.artifacts:
            assert req.type in valid_types, f"{req.id} has invalid type: {req.type}"


# ─── Inception Schema ───────────────────────────────────────────────


class TestInceptionSchema:
    def test_valid_inception(self):
        output = InceptionOutput(**FAKE_INCEPTION)
        assert output.id == "INC-001"
        assert len(output.mvp_scope.included_reqs) > 0
        assert len(output.risks) >= 1
        assert len(output.success_criteria) >= 1

    def test_mvp_scope_covers_all_reqs(self):
        """included + excluded should cover all requirement IDs."""
        output = InceptionOutput(**FAKE_INCEPTION)
        all_req_ids = set(FAKE_INCEPTION["requirement_ids"])
        covered = set(output.mvp_scope.included_reqs) | set(output.mvp_scope.excluded_reqs)
        assert covered == all_req_ids, f"MVP scope missing: {all_req_ids - covered}"

    def test_risk_has_mitigation(self):
        output = InceptionOutput(**FAKE_INCEPTION)
        for risk in output.risks:
            assert risk.mitigation, f"{risk.id} is missing mitigation strategy"

    def test_risk_impact_valid(self):
        output = InceptionOutput(**FAKE_INCEPTION)
        valid_impacts = {"high", "medium", "low"}
        for risk in output.risks:
            assert risk.impact in valid_impacts, f"{risk.id} has invalid impact: {risk.impact}"


# ─── User Story Schema ──────────────────────────────────────────────


class TestUserStorySchema:
    def test_valid_user_story(self):
        us = UserStory(**FAKE_USER_STORIES["artifacts"][0])
        assert us.id == "US-001"
        assert len(us.requirement_ids) >= 1
        assert len(us.acceptance_criteria) >= 1

    def test_user_stories_output(self):
        output = UserStoriesOutput(**FAKE_USER_STORIES)
        assert len(output.artifacts) >= 1

    def test_story_format(self):
        """Story should follow 'Como..., quiero..., para...' format."""
        output = UserStoriesOutput(**FAKE_USER_STORIES)
        for us in output.artifacts:
            story_lower = us.story.lower()
            assert "como" in story_lower, f"{us.id} story missing 'Como'"
            assert "quiero" in story_lower, f"{us.id} story missing 'quiero'"
            assert "para" in story_lower, f"{us.id} story missing 'para'"

    def test_acceptance_criteria_dado_cuando_entonces(self):
        """Acceptance criteria should use DADO/CUANDO/ENTONCES format."""
        output = UserStoriesOutput(**FAKE_USER_STORIES)
        for us in output.artifacts:
            for ac in us.acceptance_criteria:
                ac_upper = ac.upper()
                assert "DADO" in ac_upper, f"{us.id} criteria missing DADO: {ac[:50]}"
                assert "CUANDO" in ac_upper, f"{us.id} criteria missing CUANDO: {ac[:50]}"
                assert "ENTONCES" in ac_upper, f"{us.id} criteria missing ENTONCES: {ac[:50]}"

    def test_user_story_traces_to_requirements(self):
        """Each US must reference at least one REQ."""
        output = UserStoriesOutput(**FAKE_USER_STORIES)
        for us in output.artifacts:
            assert len(us.requirement_ids) >= 1, f"{us.id} has no requirement_ids"
            for req_id in us.requirement_ids:
                assert req_id.startswith("REQ-"), f"{us.id} references invalid req: {req_id}"

    def test_priority_valid(self):
        output = UserStoriesOutput(**FAKE_USER_STORIES)
        valid = {"high", "medium", "low"}
        for us in output.artifacts:
            assert us.priority in valid, f"{us.id} has invalid priority: {us.priority}"


# ─── Test Case Schema ───────────────────────────────────────────────


class TestTestCaseSchema:
    def test_valid_test_case(self):
        tc = TestCase(**FAKE_TEST_CASES["artifacts"][0])
        assert tc.id == "TC-001"
        assert tc.type in ("positive", "negative")

    def test_test_cases_output(self):
        output = TestCasesOutput(**FAKE_TEST_CASES)
        assert len(output.artifacts) >= 2

    def test_test_case_traces_to_user_story(self):
        """Each TC must reference at least one US."""
        output = TestCasesOutput(**FAKE_TEST_CASES)
        for tc in output.artifacts:
            assert len(tc.user_story_ids) >= 1, f"{tc.id} has no user_story_ids"
            for us_id in tc.user_story_ids:
                assert us_id.startswith("US-"), f"{tc.id} references invalid story: {us_id}"

    def test_test_case_traces_to_requirements(self):
        """Each TC must reference at least one REQ."""
        output = TestCasesOutput(**FAKE_TEST_CASES)
        for tc in output.artifacts:
            assert len(tc.requirement_ids) >= 1, f"{tc.id} has no requirement_ids"

    def test_test_case_has_steps(self):
        output = TestCasesOutput(**FAKE_TEST_CASES)
        for tc in output.artifacts:
            assert len(tc.steps) >= 1, f"{tc.id} has no steps"

    def test_test_case_has_expected_result(self):
        output = TestCasesOutput(**FAKE_TEST_CASES)
        for tc in output.artifacts:
            assert tc.expected_result, f"{tc.id} has no expected_result"

    def test_has_positive_and_negative(self):
        """There should be at least one positive and one negative test case."""
        output = TestCasesOutput(**FAKE_TEST_CASES)
        types = {tc.type for tc in output.artifacts}
        assert "positive" in types, "No positive test case found"
        assert "negative" in types, "No negative test case found"


# ─── Diagram Schema ─────────────────────────────────────────────────


class TestDiagramSchema:
    def test_valid_diagrams(self):
        output = DiagramsOutput(**FAKE_DIAGRAMS)
        assert output.er_diagram.mermaid_code.startswith("erDiagram")
        assert output.sequence_diagram.mermaid_code.startswith("sequenceDiagram")

    def test_er_diagram_references_reqs(self):
        output = DiagramsOutput(**FAKE_DIAGRAMS)
        assert len(output.er_diagram.referenced_reqs) >= 1

    def test_sequence_diagram_references_stories(self):
        output = DiagramsOutput(**FAKE_DIAGRAMS)
        assert len(output.sequence_diagram.referenced_stories) >= 1

    def test_diagrams_have_descriptions(self):
        output = DiagramsOutput(**FAKE_DIAGRAMS)
        assert output.er_diagram.description, "ER diagram missing description"
        assert output.sequence_diagram.description, "Sequence diagram missing description"


# ─── Full Traceability Chain ────────────────────────────────────────


class TestTraceability:
    """Verify the REQ → US → TC → Design chain is intact across all artifacts."""

    def test_full_chain(self):
        reqs = RequirementsOutput(**FAKE_REQUIREMENTS)
        stories = UserStoriesOutput(**FAKE_USER_STORIES)
        cases = TestCasesOutput(**FAKE_TEST_CASES)
        diagrams = DiagramsOutput(**FAKE_DIAGRAMS)

        req_ids = {r.id for r in reqs.artifacts}
        us_ids = {u.id for u in stories.artifacts}

        # Every US references valid REQs
        for us in stories.artifacts:
            for req_id in us.requirement_ids:
                assert req_id in req_ids, f"{us.id} references unknown {req_id}"

        # Every TC references valid USs and REQs
        for tc in cases.artifacts:
            for us_id in tc.user_story_ids:
                assert us_id in us_ids, f"{tc.id} references unknown {us_id}"
            for req_id in tc.requirement_ids:
                assert req_id in req_ids, f"{tc.id} references unknown {req_id}"

        # Diagrams reference valid REQs and USs
        for req_id in diagrams.er_diagram.referenced_reqs:
            assert req_id in req_ids, f"ER diagram references unknown {req_id}"
        for us_id in diagrams.sequence_diagram.referenced_stories:
            assert us_id in us_ids, f"Sequence diagram references unknown {us_id}"

    def test_all_seven_artifact_types_present(self):
        """The system must produce 7 artifact types."""
        reqs = RequirementsOutput(**FAKE_REQUIREMENTS)
        inception = InceptionOutput(**FAKE_INCEPTION)
        stories = UserStoriesOutput(**FAKE_USER_STORIES)
        cases = TestCasesOutput(**FAKE_TEST_CASES)
        diagrams = DiagramsOutput(**FAKE_DIAGRAMS)

        # 1. Requirements
        assert len(reqs.artifacts) >= 1
        # 2. Inception/MVP
        assert inception.id == "INC-001"
        # 3. User Stories
        assert len(stories.artifacts) >= 1
        # 4. Test Cases
        assert len(cases.artifacts) >= 1
        # 5. ER Diagram
        assert diagrams.er_diagram.mermaid_code
        # 6. Sequence Diagram
        assert diagrams.sequence_diagram.mermaid_code
        # 7. Decision log is tested in test_db.py and test_api.py
