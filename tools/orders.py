"""Outils de lecture des commandes (simulées)."""
import json
import re
from datetime import date

from config import DATA, TODAY

ORDER_ID_RE = re.compile(r"^\d{3,6}$")


def _load() -> dict:
    orders = json.loads((DATA / "orders.json").read_text(encoding="utf-8"))
    return {o["id"]: o for o in orders}


def get_order(order_id: str, customer_id: str) -> dict:
    """Retourne les FAITS d'une commande. Ne conclut rien.
    Garde-fous : format validé, et une commande d'un autre client
    est indiscernable d'une commande inexistante."""
    order_id = str(order_id).strip().lstrip("#")
    if not ORDER_ID_RE.match(order_id):
        return {"found": False, "order_id": order_id, "error": "format invalide"}
    order = _load().get(order_id)
    if not order or order["customer_id"] != customer_id:
        return {"found": False, "order_id": order_id}
    return {"found": True, **{k: v for k, v in order.items() if k != "customer_id"}}


def days_since(date_str: str) -> int:
    """Nombre de jours entre une date ISO (AAAA-MM-JJ) et aujourd'hui.
    Calcul en code : un LLM se trompe sur les dates."""
    return (TODAY - date.fromisoformat(date_str)).days
