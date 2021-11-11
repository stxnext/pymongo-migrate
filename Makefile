run=

init:
	pip install -r requirements.txt

format:
	$(run) pyupgrade --py36-plus ./**/*.py
	$(run) isort .
	$(run) black .
	$(run) flake8 .
	$(run) mypy src
	$(run) bandit -c .bandit.yml -r .

test:
	docker-compose up -d mongo
	$(run) pytest -vv
	docker-compose down

check: format test
	@echo "Everything ok!"

publish:
	pip install twine
	python setup.py sdist
	twine upload dist/*
	rm -fr build dist .egg requests.egg-info

ci:
	$(run) isort -c .
	$(run) black --check .
	$(run) flake8 .
	$(run) mypy src
	$(run) bandit -c .bandit.yml -r .
	$(run) pytest
