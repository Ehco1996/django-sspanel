.PHONY: setup update fmt check

setup:
	poetry install

update:
	poetry update

fmt:
	autoflake --recursive --remove-all-unused-imports --in-place . && isort . && black .

check:
	isort --check .
	black  --check .