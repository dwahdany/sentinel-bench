# attempts

One directory per attempt, named `<run_id>-<n>`. The runner drops whatever the attempt
produced in here: stdout/stderr, any files written under `/work`, and core dumps if the
target crashed. Large outputs arrive chunked as `part-000`, `part-001`, ... and are
meant to be reassembled in lexical order before grading.

Empty in a fresh checkout. Attempt directories are generated, never committed.
