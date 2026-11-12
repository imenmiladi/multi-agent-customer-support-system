"""Le graphe LangGraph : State partagé + nœuds + arêtes conditionnelles."""
import operator
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

import guards
from agents import HANDOFF, last_user_message, order_agent, refund_agent, supervisor


class State(TypedDict):
    messages: Annotated[list, add_messages]   # conversation
    customer_id: str                          # identité (simulée) du client
    order: dict | None                        # écrit par Order Agent
    decision: dict | None                     # écrit par Refund Agent (ou garde-fous)
    next: str                                 # écrit par Supervisor
    iterations: int                           # garde-fou anti-boucle
    steps: Annotated[list, operator.add]      # trace des nœuds exécutés
    wants_refund: bool                        # écrit par Supervisor

def input_guard_node(state):
    msg = guards.input_guard(last_user_message(state))
    if msg:
        return {"decision": {"status": "blocked", "answer": msg, "amount": None,
                             "rule_source": None}, "steps": ["input_guard"]}
    return {"steps": ["input_guard"]}


def fallback_node(state):
    return {"decision": {"status": "handoff", "answer": HANDOFF, "amount": None,
                         "rule_source": None, "why": guards.fallback_reason(state)},
            "steps": ["fallback"]}


def output_guard_node(state):
    d = state["decision"]
    allowed = {a for a in (d.get("amount"), (state.get("order") or {}).get("amount")) if a}
    ok, why = guards.output_guard_ok(d["answer"], allowed)
    if ok:
        return {"steps": ["output_guard"]}
    return {"decision": {**d, "status": "handoff", "answer": HANDOFF,
                         "why": f"garde-fou sortie: {why}"}, "steps": ["output_guard"]}


def build_graph():
    g = StateGraph(State)
    for name, fn in [("input_guard", input_guard_node), ("supervisor", supervisor),
                     ("order_agent", order_agent), ("refund_agent", refund_agent),
                     ("fallback", fallback_node), ("output_guard", output_guard_node)]:
        g.add_node(name, fn)

    g.add_edge(START, "input_guard")
    g.add_conditional_edges("input_guard",
                            lambda s: "end" if s.get("decision") else "supervisor",
                            {"end": END, "supervisor": "supervisor"})
    g.add_conditional_edges("supervisor", guards.route_guard,
                            {"order_agent": "order_agent", "refund_agent": "refund_agent",
                             "output_guard": "output_guard", "fallback": "fallback"})
    g.add_edge("order_agent", "supervisor")    # retour au chef
    g.add_edge("refund_agent", "supervisor")   # retour au chef
    g.add_edge("fallback", END)
    g.add_edge("output_guard", END)
    return g.compile()


app = build_graph()


def ask(message: str, customer_id: str = "C1", history=None) -> dict:
    msgs = list(history or []) + [HumanMessage(message)]
    return app.invoke({"messages": msgs, "customer_id": customer_id, "wants_refund": True,
                       "order": None, "decision": None, "next": "", "iterations": 0, "steps": []})