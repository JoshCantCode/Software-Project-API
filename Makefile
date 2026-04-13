.PHONY: test install

install:
	pip install -r requirements.txt
	pip install pytest pytest-flask

test:
	pytest tests/ -v

test-coverage:
	pytest tests/ -v --cov=. --cov-report=term-missing
