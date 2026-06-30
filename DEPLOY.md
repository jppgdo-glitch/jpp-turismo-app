# JPP Turismo - colocar online

Este app gera ordens de embarque e orcamentos em PDF.

## Para rodar no computador

```powershell
python app.py
```

Abra:

```text
http://127.0.0.1:8765
```

## Para colocar online

Use uma hospedagem que rode Python e aceite estes arquivos:

- `app.py`
- `requirements.txt`
- `Procfile`
- pasta `scripts/`

Configuracao:

- Build/install: `pip install -r requirements.txt`
- Start command: `python app.py`
- Variaveis:
  - `HOST=0.0.0.0`
  - `PORT` deve ser a porta fornecida pela hospedagem

Depois de publicado, abra o link no celular e use:

- Android Chrome: menu de tres pontos > Adicionar a tela inicial
- iPhone Safari: Compartilhar > Adicionar a Tela de Inicio
