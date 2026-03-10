.PHONY: build release test clean

test:
	python -m pytest tests/ -v

build: clean
	python -m build

release: build
	python -m twine upload dist/*

clean:
	rm -rf dist/ build/ *.egg-info py_Asterisk.egg-info
