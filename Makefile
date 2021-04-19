.PHONY: setup update fmt

setup:
	poetry install

update:
	poetry update

fmt:
	autoflake --recursive --remove-all-unused-imports --in-place . && isort . && black .
