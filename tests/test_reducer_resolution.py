"""Unit tests for the Reducer's conflict auto-resolution heuristic.

These pin the *behavior* of `Reducer._merge_hunk` so we can refactor the
merger without silently regressing the safety guarantees.
"""

from orchestrator.reducer import Reducer


def test_identical_sides_take_either():
    assert Reducer._merge_hunk("foo\n", "foo\n") == "foo\n"


def test_empty_side_takes_other():
    assert Reducer._merge_hunk("", "x\n") == "x\n"
    assert Reducer._merge_hunk("y\n", "") == "y\n"


def test_containment_takes_superset():
    ours = "a\n"
    theirs = "a\nb\n"
    assert Reducer._merge_hunk(ours, theirs) == theirs
    assert Reducer._merge_hunk(theirs, ours) == theirs


def test_pure_appends_after_common_prefix_are_concatenated():
    ours = "shared\nours-extra\n"
    theirs = "shared\ntheirs-extra\n"
    out = Reducer._merge_hunk(ours, theirs)
    assert out is not None
    assert "shared\n" in out
    assert "ours-extra\n" in out
    assert "theirs-extra\n" in out
    # Deterministic ordering — alphabetical tail order.
    assert out.index("ours-extra") < out.index("theirs-extra")


def test_truly_divergent_hunks_still_concatenate_when_no_shared_prefix():
    # Both sides are *entirely* different — current heuristic still produces
    # a deterministic concatenation. This documents (and intentionally pins)
    # the most permissive branch of the resolver. Real-world Workers should
    # never reach this path because the Master proves task independence
    # before fan-out — but we want the behavior to be deterministic if it
    # somehow does.
    out = Reducer._merge_hunk("alpha\n", "beta\n")
    assert out is not None
    assert "alpha" in out and "beta" in out
