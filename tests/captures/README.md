# captures

Recorded fixture traffic, RAW linktype, replayed from file by `sentinel_bench.pcap`.
Nothing here was captured from a real network: the requests were generated against the
loopback fixture container and every probe request carries an `SB_PROBE_*` marker.

Each `X.pcap` has a sidecar `X.expected.json` listing exactly the rule ids that must
fire. `dns-noise.pcap` is the negative control and must fire nothing -- a ruleset that
fires on it has a false-positive problem and the regression run should say so.
