setup:
	python3 -m venv venv
	source venv/bin/activate && pip install -r requirements.txt
	mkdir -p inputs outputs
	touch inputs/.gitkeep outputs/.gitkeep venv/.gitkeep
	echo "Environment set up."

clean:
	rm -rf venv __pycache__ .pytest_cache

freeze:
	source venv/bin/activate && pip freeze > requirements.txt

