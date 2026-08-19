from sentinel_bench.scoring import exact_match


def test_exact_match():
    assert exact_match(' A ', 'a') == 1.0
    assert exact_match('a', 'b') == 0.0
