"""Seul outil d'écriture financière. Le LLM propose, CE CODE vérifie."""
from config import HUMAN_THRESHOLD
from tools.orders import _load

_REFUNDED: set[str] = set()   # remboursements exécutés pendant la session


def reset() -> None:
    _REFUNDED.clear()


def issue_refund(order_id: str, amount: float, customer_id: str) -> dict:
    order = _load().get(str(order_id))
    if not order:
        return {"ok": False, "error": "commande introuvable"}
    if order["customer_id"] != customer_id:
        return {"ok": False, "error": "commande d'un autre client"}
    if order["already_refunded"] or order["id"] in _REFUNDED:
        return {"ok": False, "error": "déjà remboursée"}
    if amount <= 0 or amount > order["amount"]:
        return {"ok": False, "error": "montant invalide (supérieur à la commande)"}
    if amount > HUMAN_THRESHOLD:
        return {"ok": False, "needs_human": True,
                "error": "validation humaine requise (montant > 100 €)"}
    _REFUNDED.add(order["id"])
    return {"ok": True, "refund_id": f"RF-{order['id']}", "amount": amount}
