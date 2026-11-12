"""Faux LLM scripté : permet de tester tout le graphe sans clé API."""
import re

from langchain_core.messages import AIMessage, ToolMessage

from agents import Route, RefundAnswer


def _call(name, args, i):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"c{i}", "type": "tool_call"}])


class FakeLLM:
    def __init__(self, supervisor_override=None, refund_script=None, answer=None):
        self.supervisor_override = supervisor_override
        self.refund_script = refund_script          # liste d'appels d'outils
        self.answer = answer

    def with_structured_output(self, schema):
        outer = self
        class S:
            def invoke(self, msgs):
                text = "\n".join(str(m.content) for m in msgs)
                if schema is Route:
                    if outer.supervisor_override:
                        return Route(next=outer.supervisor_override, reason="forcé")
                    if "décision finale présente : oui" in text: return Route(next="FINISH", reason="ok")
                    if "order_agent déjà exécuté : non" in text: return Route(next="order_agent", reason="ok")
                    if "commande trouvée : oui" in text and "refund_agent déjà exécuté : non" in text:
                        return Route(next="refund_agent", reason="ok")
                    return Route(next="FINISH", reason="ok")
                return outer.answer or RefundAnswer(eligible=True, amount=85.0,
                       rule_source="non_livree.md", answer="Votre commande est remboursée : 85 €.")
        return S()

    def bind_tools(self, tools):
        outer = self
        class T:
            def invoke(self, msgs):
                is_order = "Order Agent" in msgs[0].content
                n = sum(isinstance(m, ToolMessage) for m in msgs)
                if is_order:
                    m = re.search(r"\d{3,6}", msgs[1].content)
                    if n == 0 and m:
                        return _call("get_order", {"order_id": m.group()}, n)
                    return AIMessage(content="fini")
                script = outer.refund_script or [
                    ("search_policy", {"query": "commande non livrée remboursement"}),
                    ("days_since", {"date_iso": "2026-10-14"}),
                    ("issue_refund", {"amount": 85.0})]
                if n < len(script):
                    return _call(*script[n], n)
                return AIMessage(content="fini")
        return T()
