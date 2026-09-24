.PHONY: test install-dev

install-dev:
	python -m pip install -r requirements-dev.txt

test: install-dev
	python -m pytest --cov=plugins/module_utils --cov=plugins/modules --cov-branch --cov-report=term-missing --cov-fail-under=100
