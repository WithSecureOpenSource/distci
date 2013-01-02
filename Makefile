dist:
	python setup.py bdist_egg

sdist:
	python setup.py sdist

tests:
	nosetests -v

clean:
	rm -rf dist distci.egg-info build

pylint:
	python -m pylint.lint src/frontend/*.py

