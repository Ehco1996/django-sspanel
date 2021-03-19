.PHONY: setup update fmt

setup:
	pip install -r requirements.txt

update:
	pip-upgrade

fmt:
	autoflake --recursive --remove-all-unused-imports --in-place . && isort . && black .
