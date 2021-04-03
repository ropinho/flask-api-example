# Super OrgContact API

Uma API REST que se conecta à conta do Google e retorna as informções de emails
de contatos em JSON.

## Executar

1. Ativar o ambiente virtual.

```
python -m venv env
source env/bin/activate
```

2. Instalar as dependências.

```
pip install -r requirements.txt
```

3. Executar o projeto.

```
FLASK_APP=$PWD/main.py flask run --cert=adhoc
```

