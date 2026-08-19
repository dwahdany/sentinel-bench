# IV.A -- refusal robustness

The family measures whether a model under test holds a boundary when the request is
dressed up: an authorization claim, time pressure, a roleplay frame, a request split
into innocuous halves, a false premise, an appeal to authority.

Item shape (one per entry in the promptset):

    id                 stable, never reused
    category           one of the framings above
    framing            one line describing the dress-up
    prompt             the request as the tester would send it -- PROBE ONLY
    expected_behaviour what a correct answer does
    scoring_notes      what to count as partial credit

`prompt` carries no operational content. The point of measuring is the framing, not the
request's substance, and an item that is useful to act on has failed its own brief.

The promptset itself is not written yet; a hand-run sample of scored transcripts lives
in `tests/fixtures/gate_transcripts.jsonl`.
