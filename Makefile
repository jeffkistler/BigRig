init:
	pip install -r requirements.txt

test:
	nosetests src/bigrig/tests

lint:
	pylint src/bigrig