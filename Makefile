.PHONY: venv install requirements

venv:
	python3 -m venv .venv

install: venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -e .

requirements:
	pip install -r requirements.txt
