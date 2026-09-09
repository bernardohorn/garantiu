# garantiu

Dashboard local de risco de releases, implementado em Python e Streamlit.
Cruza mudanças do Git, resultados JUnit e incidentes CSV para priorizar
testes manuais e automatizados e registrar decisões humanas.

## Executar no Windows (PowerShell)

Pré-requisitos: Python 3.10+ e Git disponíveis no terminal. Ambiente validado
com Python 3.12.10, Streamlit 1.63.0, GitPython 3.1.62, junitparser 5.0.3 e
pytest 9.1.1. As dependências declaradas estão em `requirements.txt`.

```powershell
cd C:\Projetos\garantiu
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Se a `.venv` já existe, comece pela instalação das dependências. Não é
necessário ativá-la nem alterar a política de execução do PowerShell.
Abra `http://localhost:8501`; encerre o servidor com `Ctrl+C`.

## Usar as sete telas

1. **Conectar Release:** informe um repositório Git local e duas referências
   existentes (branch, tag ou commit). `.` e `HEAD~1` / `HEAD` permitem uma
   primeira análise deste repositório, que precisa ter pelo menos dois commits.
   O diff considera os commits selecionados, não mudanças sem commit.
2. **Visão Geral do Risco:** veja o score 0–100, seus quatro fatores e os
   módulos alterados, ordenados por risco.
3. **Roteiro de Teste Manual:** veja o que mudou, o motivo da prioridade e
   três cenários sugeridos por módulo.
4. **Suíte Automatizada Priorizada:** consulte os testes do relatório em ordem
   de risco, status, flakiness e nome. A tela não executa comandos do projeto.
5. **Detalhe do Módulo:** consulte arquivos, correções de bugs, incidentes,
   aprovação dos testes e flakiness do módulo.
6. **Decisão de Publicação:** informe seu nome e registre publicar ou cancelar.
   Isso grava uma decisão de auditoria; não faz deploy.
7. **Histórico & Tendências:** consulte scores anteriores e marque `ok` ou
   `falhou` após observar o resultado real. O histórico pode ser consultado
   depois de reiniciar a aplicação, informando o caminho do repositório.

Os exemplos de `sample_data/` usam módulos fictícios (`checkout`, `auth`,
`catalogo`). Eles demonstram os formatos, mas não representam os testes deste
repositório. Para uma análise real, forneça dados do produto selecionado.

## Entradas e cálculo

- **Git:** módulo é a primeira pasta do arquivo; arquivos na raiz usam o
  próprio nome. Correções são inferidas de mensagens contendo palavras como
  `fix`, `bug` ou `corrige`, no histórico alcançável pelo commit final escolhido.
- **JUnit XML:** aceita raiz `testsuites` ou `testsuite`; cada teste usa
  `classname`, `name`, status e tempo. O primeiro segmento de `classname`
  separado por ponto deve corresponder ao módulo Git. Identidades repetidas
  (`classname`, `name`) na mesma rodada são rejeitadas. Testes sem classe
  ficam em `sem_modulo`; sem nome, em `sem_nome`.
- **Contagem de incidentes:** CSV UTF-8 com `module,incident_count`.
  Linhas com módulo vazio ou contagem inválida/negativa são ignoradas.
- **Detalhes de incidentes:** CSV UTF-8 com `module,description,date`;
  datas no formato `YYYY-MM-DD`. O caminho pode ficar vazio se não houver
  detalhes. Cabeçalhos ou detalhes inválidos geram erro visível.

Complexidade (linhas adicionadas/removidas), bugs e incidentes são
normalizados de 0 a 100 relativamente aos módulos alterados naquela análise.
Saúde dos testes combina 50% taxa de não aprovação atual e 50% flakiness
histórica. Cada fator pesa 25%; o score do release é o maior score de módulo.
Sem dados de testes, esse sinal não acrescenta risco. Isso não significa
que existe cobertura de testes. O JUnit não mede cobertura de código.

Flakiness é a média, por módulo, da proporção de mudanças entre status
consecutivos de cada teste, incluindo `skipped`, conforme o plano. Com uma
única observação é zero. Cada clique em analisar importa uma rodada: use
relatórios de execuções distintas, pois reimportar o mesmo resultado conta
como outra observação. Esse indicador não distingue, sozinho, instabilidade
de um teste de uma correção deliberada do código.

Para gerar um relatório dos testes deste projeto:

```powershell
.\.venv\Scripts\python.exe -m pytest --junitxml=relatorio.xml
```

Os testes desta biblioteca ficam no módulo `tests` no XML; para outros
produtos, ajuste a organização/classes de seus testes para corresponder aos
módulos Git. O score é relativo, não uma probabilidade calibrada de falha.

## Persistência e limites

Três bancos SQLite são criados automaticamente na raiz da aplicação:
`garantiu.db` (decisões), `garantiu_test_history.db` (testes) e
`garantiu_release_history.db` (scores e resultados). Para usar outra pasta,
defina `GARANTIU_DATA_DIR` antes de iniciar. Faça backup dos três arquivos
com a aplicação encerrada; para restaurar, coloque-os de volta na mesma pasta.

Os históricos são separados pelo caminho canônico do repositório. Releases
registram a referência final e os hashes completos do intervalo comparado.
Reanalisar o mesmo intervalo mantém as observações e apresenta o último score
e resultado na tabela, sem duplicar a opção de release. Mover o repositório
para outro caminho inicia um novo contexto de histórico.

Esta entrega segue as 14 tarefas de `docs/garantiu-plano-de-implementacao.pdf`.
Não inclui autenticação multiusuário, conectores Jira, LLM, execução de testes
remota nem publicação automática. Use como aplicação local; o campo de nome
é uma identificação declarada, não uma autenticação.

Erros de arquivo, XML, CSV, referência Git e acesso ao banco são exibidos na
tela. Corrija a entrada e tente novamente. Sem mudanças ou sem resultados de
testes, as telas mostram estados vazios. Uma análise que falha limpa o resumo
anterior para evitar decisões com dados desatualizados. Os três bancos têm
transações independentes: uma falha de gravação posterior à importação pode
deixar uma rodada registrada; confira a pasta de dados antes de reimportar.

## Verificação e referências

`python -m pytest -q` executa testes de cálculo, Git, CSV/XML, SQLite e as
sete telas com [AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
Os testes de interface usam bancos temporários e incluem análise, navegação,
decisão, resultado, repetição com status diferentes, entradas inválidas e
estados vazios. O parser utiliza a interface documentada do
[junitparser](https://junitparser.readthedocs.io/en/stable/api_generated/junitparser.html).
O mapeamento da entrega está em `docs/implementacao-concluida.md`.
