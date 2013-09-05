
clean:
	rm -rf .gitignore
	find . -name '*.pyc' -delete

test:
	./manage.py test {{ project_name }}

run:
	./manage.py runserver 0:8000
