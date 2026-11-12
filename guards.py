"""Garde-fous en CODE (le prompt guide, le code garantit)."""
import re

from config import MAX_ITERATIONS

# ---------- 1. Entrée ----------
INJECTION = re.compile(
    r"ignore (all|previous|tes|your)|oublie (tes|toutes)|system prompt|"
    r"prompt syst[eè]me|tu es maintenant|sans v[ée]rifier", re.I)


def input_guard(text: str) -> str | None:
    """Retourne un message de refus, ou None si l'entrée est acceptable."""
    if len(text) > 1000:
        return "Votre message est trop long. Pouvez-vous le résumer ?"
    if INJECTION.search(text):
        return "Je ne peux pas traiter cette demande."
    return None


# ---------- 2. Routage ----------
VALID_NEXT = {"order_agent", "refund_agent", "FINISH"}


def fallback_reason(state: dict) -> str | None:
    """Pourquoi on abandonne le chemin normal (None = tout va bien)."""
    nxt, steps = state.get("next"), state.get("steps", [])
    if state.get("iterations", 0) > MAX_ITERATIONS:
        return "max_iterations"
    if nxt not in VALID_NEXT:
        return "invalid_next"
    if nxt == "FINISH" and not state.get("decision"):
        return "finish_without_decision"
    if nxt in ("order_agent", "refund_agent") and nxt in steps:
        return f"loop_{nxt}"                     # même agent rappelé : boucle
    if nxt == "refund_agent" and not state.get("order"):
        return "refund_without_order"
    return None


def route_guard(state: dict) -> str:
    if fallback_reason(state):
        return "fallback"
    return "output_guard" if state["next"] == "FINISH" else state["next"]


# ---------- 5. Sortie ----------
AMOUNT_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:€|euros?)", re.I)
FORBIDDEN = re.compile(r"garanti|sous 24 ?h|imm[ée]diatement|sans condition", re.I)


def output_guard_ok(reply: str, allowed_amounts: set[float]) -> tuple[bool, str]:
    for raw in AMOUNT_RE.findall(reply):
        val = float(raw.replace(",", "."))
        if not any(abs(val - a) < 0.01 for a in allowed_amounts):
            return False, f"montant incohérent: {val}"
    if FORBIDDEN.search(reply):
        return False, "promesse non autorisée"
    return True, ""
