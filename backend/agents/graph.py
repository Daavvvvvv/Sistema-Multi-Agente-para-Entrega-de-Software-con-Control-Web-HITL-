"""LangGraph pipeline definition."""

from agents.state import PipelineState

# TODO: Build the LangGraph StateGraph with nodes for each agent
# and conditional edges for HITL gates.
#
# Flow:
# brief → ba_agent → hitl_1 → product_agent → hitl_2 → analyst_agent → hitl_3 → qa_agent → design_agent → hitl_4 → done
