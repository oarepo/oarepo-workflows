black oarepo_workflows tests --target-version py310
autoflake --in-place --remove-all-unused-imports --recursive oarepo_workflows tests
isort oarepo_workflows tests  --profile black
