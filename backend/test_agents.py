"""Quick test: run QA and Design agents with fake data from previous agents."""

import asyncio
import json

from database import init_db
from services.db_service import create_run
from agents.qa_agent import run_qa_agent
from agents.design_agent import run_design_agent

# Fake output from BA agent
FAKE_REQUIREMENTS = {
    "artifacts": [
        {"id": "REQ-001", "title": "User Registration", "description": "Users must be able to register with email and password", "type": "functional", "priority": "high", "actors": ["User"]},
        {"id": "REQ-002", "title": "Product Catalog", "description": "System must display a list of available products with prices", "type": "functional", "priority": "high", "actors": ["User", "Admin"]},
        {"id": "REQ-003", "title": "Shopping Cart", "description": "Users can add products to a cart and modify quantities", "type": "functional", "priority": "medium", "actors": ["User"]},
    ],
    "domain_summary": "E-commerce platform",
    "assumptions": ["Users have internet access", "Payment processing is handled by a third party"],
}

# Fake output from Product agent
FAKE_INCEPTION = {
    "id": "INC-001",
    "mvp_scope": {"included_reqs": ["REQ-001", "REQ-002", "REQ-003"], "excluded_reqs": [], "justification": "All requirements are core for MVP"},
    "risks": [{"id": "RISK-001", "description": "Third-party payment API downtime", "impact": "high", "mitigation": "Implement retry logic"}],
    "success_criteria": ["Users can register and browse products", "Users can add items to cart"],
}

# Fake output from Analyst agent
FAKE_USER_STORIES = {
    "artifacts": [
        {"id": "US-001", "title": "User registration", "requirement_ids": ["REQ-001"], "story": "Como usuario, quiero registrarme con email y contraseña, para acceder a la plataforma", "acceptance_criteria": ["DADO que estoy en la pagina de registro CUANDO ingreso email y contraseña validos ENTONCES se crea mi cuenta"], "priority": "high", "estimation": "3 SP"},
        {"id": "US-002", "title": "Browse products", "requirement_ids": ["REQ-002"], "story": "Como usuario, quiero ver el catalogo de productos, para elegir que comprar", "acceptance_criteria": ["DADO que estoy logueado CUANDO accedo al catalogo ENTONCES veo la lista de productos con precios"], "priority": "high", "estimation": "5 SP"},
        {"id": "US-003", "title": "Add to cart", "requirement_ids": ["REQ-003"], "story": "Como usuario, quiero agregar productos al carrito, para comprarlos despues", "acceptance_criteria": ["DADO que veo un producto CUANDO hago click en agregar ENTONCES el producto aparece en mi carrito"], "priority": "medium", "estimation": "3 SP"},
    ]
}


async def main():
    await init_db()

    # Create a test run
    run = await create_run("Test brief: E-commerce platform with registration, catalog, and cart")
    run_id = run["id"]
    print(f"Created test run: {run_id}\n")

    # Build the pipeline state as if previous agents already ran
    state = {
        "run_id": run_id,
        "brief": "E-commerce platform with registration, catalog, and cart",
        "current_stage": "qa",
        "requirements": FAKE_REQUIREMENTS,
        "inception": FAKE_INCEPTION,
        "user_stories": FAKE_USER_STORIES,
        "test_cases": None,
        "diagrams": None,
        "hitl_status": None,
        "hitl_feedback": None,
        "error": None,
        "retry_count": 0,
    }

    # Run QA agent
    print("=" * 60)
    print("Running QA Agent...")
    print("=" * 60)
    qa_result = await run_qa_agent(state)
    print(json.dumps(qa_result, indent=2, ensure_ascii=False))

    # Update state with QA output
    state["test_cases"] = qa_result["test_cases"]

    # Run Design agent
    print("\n" + "=" * 60)
    print("Running Design Agent...")
    print("=" * 60)
    design_result = await run_design_agent(state)
    print(json.dumps(design_result, indent=2, ensure_ascii=False))

    print("\nBoth agents ran successfully!")
    print(f"Check the DB for run_id={run_id} to see saved artifacts and decision logs.")


if __name__ == "__main__":
    asyncio.run(main())
