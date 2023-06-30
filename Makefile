run=

init:
	pip install -r requirements.txt

format:
	$(run) black .
	$(run) ruff check --fix .
	$(run) mypy src
	$(run) bandit -c .bandit.yml -r src

test:
	docker-compose up -d mongo
	$(run) pytest -vv
	docker-compose down

check: format test
	@echo "Everything ok!"

clean:
	rm -fr build dist .egg src/pymongo_migrate.egg-info

publish: clean
	python -m pip install twine build
	python -m build
	python -m twine upload dist/*

ci:
	$(run) black --check .
	$(run) ruff check .
	$(run) mypy src
	$(run) bandit -c .bandit.yml -r src
	$(run) pytest
