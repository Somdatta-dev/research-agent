from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.agent.nodes.dedup import dedup_node
from app.agent.nodes.deliver import deliver_node, soft_fail_node
from app.agent.nodes.enrich import enrich_one_node
from app.agent.nodes.plan import plan_node
from app.agent.nodes.render_pdf import render_pdf_node
from app.agent.nodes.research import research_one_node
from app.agent.nodes.synthesize import synthesize_node
from app.agent.nodes.write import write_node
from app.agent.state import ReportState

DEDUP_MIN_HITS = 3
ENRICH_TOP_N = 12


def fan_out_to_research(state: ReportState) -> list[Send]:
    return [
        Send("research_one", {"subtopic": s, "config": state["config"]})
        for s in state["plan"]
    ]


def route_after_dedup(state: ReportState) -> list[Send] | str:
    hits = state.get("deduped_hits", [])
    if len(hits) < DEDUP_MIN_HITS:
        return "soft_fail"
    ranked = sorted(hits, key=lambda h: h.get("score", 0), reverse=True)[:ENRICH_TOP_N]
    return [
        Send("enrich_one", {"hit": h, "config": state["config"]})
        for h in ranked
    ]


def build_graph() -> StateGraph:
    graph = StateGraph(ReportState)

    graph.add_node("plan", plan_node)
    graph.add_node("research_one", research_one_node)
    graph.add_node("dedup", dedup_node, defer=True)
    graph.add_node("enrich_one", enrich_one_node)
    graph.add_node("synthesize", synthesize_node, defer=True)
    graph.add_node("write", write_node)
    graph.add_node("render_pdf", render_pdf_node)
    graph.add_node("deliver", deliver_node)
    graph.add_node("soft_fail", soft_fail_node)

    graph.add_edge(START, "plan")
    graph.add_conditional_edges("plan", fan_out_to_research, ["research_one"])
    graph.add_edge("research_one", "dedup")
    graph.add_conditional_edges("dedup", route_after_dedup, ["enrich_one", "soft_fail"])
    graph.add_edge("enrich_one", "synthesize")
    graph.add_edge("synthesize", "write")
    graph.add_edge("write", "render_pdf")
    graph.add_edge("render_pdf", "deliver")
    graph.add_edge("deliver", END)
    graph.add_edge("soft_fail", END)

    return graph
