
# Delanté Leads — MVP Streamlit

App simples para consulta de leads B2B no celular.

## O que faz
- Lê a base `leads_base.xlsx`
- Permite filtrar por cidade, tipologia, bairro e status
- Exibe leads em cards mobile-first
- Botões para Maps, ligação e WhatsApp
- Permite vendedor registrar:
  - status
  - potencial percebido
  - observação/devolutiva
  - próxima ação
  - data da visita
- Salva devolutivas em `feedback_vendedores.csv`

## Como rodar localmente

1. Instale Python 3.10+
2. Na pasta do projeto, rode:

```bash
pip install -r requirements.txt
streamlit run app.py
```

3. O app abrirá no navegador.

## Como usar no celular

Se rodar em um computador na mesma rede:
- o Streamlit mostra um endereço `Network URL`
- abra esse link no celular

## Observação importante
Esta versão salva as devolutivas em um arquivo CSV local.
Para uso com vários vendedores ao mesmo tempo e acesso externo, o ideal é evoluir para:
- banco SQLite/Postgres, ou
- Google Sheets como backend, ou
- Supabase/Firebase.
