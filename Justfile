set windows-shell := ["pwsh.exe", "-c"]
set dotenv-filename := ".env"

export PYTHONPATH := "src"

remove := if "$(expr substr $(uname -s) 1 5)" == "Linux" { "rm -rf" } else { "rmdir" }

run-local:
   poetry run python src/main.py

run-docker:
   docker-compose up --build

test path="tests/transport/routers/admin/test_post_product.py":
    export PYTHONPATH=src
    python -m poetry run pytest {{path}}

poetry-export:
    poetry export  --without-hashes -f requirements.txt -o requirements.txt

pre-commit-all:
    pre-commit run --all-files --show-diff-on-failure

lint:
    black --line-length=120 --exclude '^.+\.md$' .
    ruff-format .
    find . -name '*.py' | xargs pyupgrade --py312-plus
    ruff --fix --exclude '^(tests).+(mock|util|constant).*(\.py)$' .

alembic-gen:
    alembic revision --autogenerate
    alembic upgrade head

alembic-drop:
	alembic downgrade base
	{{ remove }} migrations/versions/*

recreate-db: alembic-drop && alembic-gen fill-db
