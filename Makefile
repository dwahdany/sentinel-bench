.PHONY: test lint fmt gate clean

test:
	uv run pytest -q

lint:
	uv run ruff check sentinel_bench scripts harness

fmt:
	uv run ruff format sentinel_bench scripts harness tests

gate:
	uv run pytest -q -m release

clean:
	rm -rf .pytest_cache out/index out/summary
