"""``sentinel-bench`` command line entry point.

``run`` executes a family; ``shell`` drops into the operator prompt loop, which is the
interactive surface people actually use when triaging a bad night.
"""

from __future__ import annotations

import argparse
import sys

from sentinel_bench import __version__, report, runlog

PROMPT = "sentinel> "
BANNER = f"sentinel-bench {__version__} -- type 'help' or 'quit'"


def run_family(family, attempts=1, out=None):
    """Placeholder driver: the real one lives in scripts/run_family.py."""
    print(f"family {family}: {attempts} attempt(s) -> {out or 'runs/'}")
    return 0


def prompt_loop(stdin=None, stdout=None):
    """The operator prompt loop. One line in, one action out, no history file."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    print(BANNER, file=stdout)
    while True:
        print(PROMPT, end="", file=stdout, flush=True)
        line = stdin.readline()
        if not line:
            return 0
        command = line.strip()
        if command in ("quit", "exit"):
            return 0
        if command == "help":
            print("commands: help, families, quit", file=stdout)
        elif command == "families":
            print("II.A II.B II.C II.D III.A IV.A", file=stdout)
        elif command:
            print(f"unknown command: {command!r}", file=stdout)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sentinel-bench")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run one task family")
    run.add_argument("--family", required=True)
    run.add_argument("--attempts", type=int, default=1)
    run.add_argument("--out", default=None)

    summary = sub.add_parser("summary", help="summarise a run log")
    summary.add_argument("path")

    sub.add_parser("shell", help="operator prompt loop")

    args = parser.parse_args(argv)
    if args.command == "run":
        return run_family(args.family, args.attempts, args.out)
    if args.command == "summary":
        records = list(runlog.read_records(args.path))
        print(f"{len(records)} records, pass rate {report.pass_rate(records):.2f}")
        return 0
    return prompt_loop()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
