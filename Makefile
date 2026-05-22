.PHONY: install test serve docker docker-run clean

PYTHON ?= python3

install:
	$(PYTHON) -m pip install -r backend/requirements.txt

test:
	cd backend && $(PYTHON) -m pytest tests/ -v

serve:
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --port 8000

docker:
	docker build -t taskflow:local .

docker-run:
	docker compose up --build

clean:
	rm -rf backend/__pycache__ backend/.pytest_cache backend/.coverage
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -f backend/taskflow.db
