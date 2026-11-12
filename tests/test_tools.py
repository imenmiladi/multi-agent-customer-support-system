from tools import orders, policy_rag, refunds


def setup_function(_):
    refunds.reset()


def test_get_order_ok_and_ownership():
    assert orders.get_order("1042", "C1")["found"]
    assert not orders.get_order("1046", "C1")["found"]       # commande d'un autre client
    assert not orders.get_order("abc", "C1")["found"]        # format invalide


def test_days_since():
    assert orders.days_since("2026-10-14") == 20


def test_refund_guards():
    assert refunds.issue_refund("1042", 85.0, "C1")["ok"]
    assert refunds.issue_refund("1042", 85.0, "C1")["error"] == "déjà remboursée"
    assert not refunds.issue_refund("1046", 30.0, "C1")["ok"]          # autre client
    assert not refunds.issue_refund("1043", 999.0, "C1")["ok"]         # > commande
    assert refunds.issue_refund("1045", 150.0, "C1")["needs_human"]    # > 100 €
    assert refunds.issue_refund("1044", 60.0, "C1")["error"] == "déjà remboursée"


def test_rag_finds_right_rule(monkeypatch):
    monkeypatch.setenv("RAG_BACKEND", "tfidf")
    policy_rag.get_index.cache_clear()
    top = policy_rag.search("commande non livrée remboursement")[0]
    assert top["source"] == "non_livree.md"
    assert policy_rag.search("recette de pizza")[0]["score"] < policy_rag.min_score()
