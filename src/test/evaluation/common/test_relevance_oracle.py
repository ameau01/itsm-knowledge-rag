"""Relevance oracle integrity tests — run against the real catalog.json."""

from __future__ import annotations

from evaluation.common.relevance import LENIENT, STRICT


def test_total_corpus_is_745(oracle):
    assert len(oracle.all_ticket_ids) == 745


def test_known_cluster_size_and_mapping(oracle):
    rc = "AIT/expired-api-token-auth-failures"
    assert len(oracle._rc[rc]) == 18
    assert oracle.root_cause_of("INC-AIT-0001") == rc


def test_strict_is_subset_of_lenient(simple_queries, oracle):
    for q in simple_queries:
        strict = oracle.relevant_tickets(q, STRICT)
        lenient = oracle.relevant_tickets(q, LENIENT)
        assert strict, f"{q.query_id} has empty strict relevance"
        assert strict <= lenient  # a root-cause cluster lives inside its family


def test_expected_ticket_set_within_cluster(simple_queries, oracle):
    """Any query carrying an expected_ticket_set must have it sit inside the query's
    root-cause cluster — otherwise a perfect retriever could not surface it."""
    for q in simple_queries:
        if not q.expected_ticket_set:
            continue
        strict = oracle.relevant_tickets(q, STRICT)
        assert set(q.expected_ticket_set) <= strict


def test_counts_match_frozen_set(simple_queries, complex_queries, abstention_queries):
    assert len(simple_queries) == 63
    assert len(complex_queries) == 34
    assert len(abstention_queries) == 15


def test_complex_queries_are_multi_label(complex_queries):
    assert all(q.is_multi_label for q in complex_queries)


def test_abstention_queries_have_no_ground_truth(abstention_queries):
    assert all(q.expected_root_cause == [] for q in abstention_queries)
