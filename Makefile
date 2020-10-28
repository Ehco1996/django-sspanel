.PHONY: setup update fmt publish

fmt:
	autoflake --recursive --remove-all-unused-imports --in-place . && isort . && black .
