# Implementação do plano

Referência: `garantiu-plano-de-implementacao.pdf` (37 páginas), com fonte
Markdown em `superpowers/plans/2026-09-09-garantiu-mvp-implementation.md`.
O PDF define o escopo técnico de sete telas; o wireframe e o relatório de
funcionalidades descrevem também ideias que não fazem parte dessas 14 tarefas.

| Tarefas | Entrega | Evidência automatizada |
|---|---|---|
| 1–2 | Diff Git, mineração de correções | `test_git_reader.py`, `test_bug_history.py` |
| 3–4 | JUnit e contagem de incidentes CSV | `test_test_reports.py`, `test_incidents.py` |
| 5–6 | Score ponderado, máximo por release e roteiro manual | `test_scoring.py`, `test_manual_test_guide.py` |
| 7–8 | Auditoria e quatro telas originais | `test_decision_log.py`, `test_app_smoke.py` |
| 9 | Rodadas SQLite e flakiness por mudanças de status | `test_test_history.py` |
| 10 | Priorização por score, status, flakiness e nome | `test_test_prioritization.py` |
| 11 | Bugs e incidentes detalhados com datas | `test_bug_history.py`, `test_incidents.py` |
| 12 | Agregação do detalhe de módulo | `test_module_detail.py` |
| 13 | Score previsto e resultado real persistidos | `test_release_history.py` |
| 14 | Sete telas integradas e histórico ligado ao score | `test_app_smoke.py` |

## Ajustes necessários ao exemplo do plano

- Preservada a fórmula e o contrato público das tarefas já implementadas.
- Histórico isolado por caminho do repositório; identidade do release inclui
  os hashes base/final para não misturar análises de intervalos distintos.
- Histórico de bugs respeita o commit final analisado, mesmo que outra branch
  esteja em checkout. As telas de detalhe usam os dados capturados na análise.
- Histórico apresenta somente o último score e resultado de cada release,
  com desempate por id quando datas são iguais; os registros anteriores ficam
  preservados no SQLite.
- Importação de uma rodada é atômica; testes duplicados e status inválidos
  são rejeitados antes de gravar. Resultados reais exigem um release existente.
- Validação de entrada, estados vazios e erros recuperáveis na interface;
  nome em branco não registra decisão. Testes de UI usam dados temporários.
- Gráfico temporal dos scores e tabela com o resultado observado. Ausência
  de resultado real continua desconhecida, sem ser convertida em sucesso.

## Limites mantidos

Os quatro fatores continuam com peso igual, sem recalibração automática.
JUnit fornece status, não cobertura. Flakiness usa todo o histórico importado
e as mudanças de status do algoritmo da Task 9, sem janela de 30 dias.
O roteiro é baseado em templates. A suíte recomenda uma ordem e as decisões
são registros, sem execução de testes ou deploy. Não há autenticação ou
integrações externas. Esses recursos não integram a implementação exigida
pelo código e pelos testes das 14 tarefas do PDF.

Instruções de execução, formatos, persistência e verificação: `../README.md`.

## Ajustes de interface e persistência

O roteiro `plano-ajustes-interface-persistencia.md` também foi implementado:

- a marca usa somente PNGs transparentes, combinando símbolo e nome sem caixas
  claras no tema escuro;
- os cabeçalhos numerados foram removidos e o campo de repositório inicia vazio;
- JUnit e os dois formatos de incidentes são explicados na primeira tela, que
  oferece os CSVs de `sample_data/` como modelos para download;
- cada análise grava, em uma transação, o score da release, os quatro fatores
  por módulo, as correções relacionadas aos arquivos e os incidentes importados;
- reanálises do mesmo intervalo são preservadas como snapshots, enquanto o
  resumo continua exibindo somente a versão mais recente;
- o histórico pode ser filtrado por release e módulo e exportado, em memória,
  como CSV UTF-8 de releases, bugs ou incidentes;
- a apresentação usa datas brasileiras, horário de São Paulo e scores com uma
  casa decimal, sem alterar timestamps ISO ou valores numéricos persistidos.
- a barra lateral permite escolher a pasta de armazenamento local; os três
  bancos SQLite passam a ser criados e consultados nesse local na sessão atual.
- a primeira tela descobre relatórios JUnit e CSVs de incidentes pelo conteúdo,
  preenche candidatos únicos e oferece escolha quando encontra vários arquivos;
  a mesma descoberta funciona para arquivos versionados em links GitHub.

## Validação desta entrega

- `python -m pytest -q`: **142 testes passaram** (Python 3.12.10), incluindo
  migrações aditivas, rollback atômico, filtros, exportações e apresentação.
- `python -m pytest -q --cov=garantiu --cov-report=term-missing`: **96% de
  cobertura de linha** no pacote `garantiu`.
- Servidor Streamlit iniciado em `127.0.0.1:8502`; endpoint
  `/_stcore/health` retornou `ok`.
- As sete telas foram exercitadas com AppTest, incluindo dados preenchidos,
  publicação/cancelamento, resultado real e nova sessão lendo o histórico.
- Inspeção visual realizada no Chrome em viewports de 1440 × 1000 e 390 × 844,
  sem overlay de erro ou mensagens de erro do navegador. O campo inicial vazio,
  a responsividade e a transparência dos logos foram conferidos.
- CI (`.github/workflows/tests.yml`) roda a mesma suíte com cobertura a cada
  push/PR para `main`, sem depender de configuração local de identidade Git
  (as fixtures de teste que criam commits configuram um autor local via
  `tests/conftest.py`, em vez de depender do `git config` global da máquina).
