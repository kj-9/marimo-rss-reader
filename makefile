
.PHONY: build
build:
	.venv/bin/marimo export html-wasm --mode run --no-show-code main.py -o dist
	@du -sh dist

.PHONY: fmt
fmt:
	ruff format .
	ruff check . --fix