Useful commands when working on pecoregex
Intended audience: pecoregex developers

Run tests:
```bash
python -m venv .venv
source .venv/bin/activate
.venv/bin/pylint --rcfile=pylintrc src/pecoregex | less
pip install -e .
pytest -q
```

Convert schema.yaml to schema.json:
```bash
yaml_json_one_liner='import sys, yaml, json; d=yaml.safe_load(sys.stdin.read()); print(json.dumps(d, indent="\t"))'
python3 -c "${yaml_json_one_liner}" < schema.yaml | sed 's/schema.yaml/schema.json/g' > schema.json
```

Validate example documents against the pecoregex document schema:
```bash
npm install pajv
for doc in document/v1/examples/*.yaml; do
	./node_modules/.bin/pajv -s document/v1/schema.yaml -d "${doc}"
done
```

Build pecoregex:
```bash
pip install build
python -m build
```

Push pecoregex to Python repositories:
```bash
python -m twine upload --repository testpypi dist/*
python -m twine upload --repository pypi dist/*
```
