
to run the venv 
``` sh
python3 -m venv .venv
```

using uv
``` sh
uv venv create .venv
```

to run the api of the DB_manager :

``` sh
uv run uvicorn main:app --reload
```