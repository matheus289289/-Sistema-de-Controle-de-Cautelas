📋 Sistema de Controle de Cautelas

Sistema desktop desenvolvido em Python para gerenciamento do ciclo de vida de empréstimo de equipamentos em organizações militares.


Sobre o Projeto

Uma cautela é o termo militar para o registro formal de empréstimo de material. Este sistema substitui o processo manual em papel, centralizando o controle de equipamentos, automatizando a geração de documentos e mantendo histórico rastreável de todas as movimentações.


Funcionalidades


Cadastro de equipamentos — registro com número patrimonial único, nome/modelo e setor
Emissão de cautela — criação de termo de recebimento com múltiplos equipamentos por operação
Geração de PDF — documento oficial formatado conforme padrão da OM, com assinatura e etiqueta destacável
Código de barras — geração automática de código Code128 via UUID, vinculado à cautela
Devolução por leitura de código — baixa de equipamento via leitora ou digitação do código de barras
Histórico completo — log de todas as saídas e devoluções com posto, NIP, responsável e datas
Dashboard em tempo real — gráfico de pizza embutido exibindo disponibilidade dos equipamentos
Importação/exportação CSV — inventário e histórico exportáveis e importáveis via planilha
Busca e filtros — pesquisa em tempo real por nome, patrimônio ou responsável



Tecnologias

CamadaTecnologiaInterface gráficaPython tkinter + ttkBanco de dadosSQLite3Geração de PDFReportLabCódigo de barraspython-barcode (Code128) + PillowDashboardMatplotlib (embutido via FigureCanvasTkAgg)Identificação únicauuid (stdlib)EmpacotamentoPyInstaller (--onefile --windowed)


Estrutura do Banco de Dados

produtos

ColunaTipoDescriçãoidINTEGER PKIdentificador internopatrimonioTEXT UNIQUENúmero patrimonial do equipamentonomeTEXTNome e modelosetorTEXTSetor de origemresponsavelTEXTResponsável atual (quando em cautela)statusTEXTDisponivel ou Indisponivelcodigo_cautelaTEXTUUID vinculado à cautela ativa

historico

ColunaTipoDescriçãoidINTEGER PKIdentificador do registropatrimonioTEXTPatrimônio do equipamentonome_equipamentoTEXTNome do equipamentopostoTEXTPosto/graduação do responsávelnipTEXTNIP do responsávelresponsavelTEXTNome completodata_saidaTEXTData e hora da saídadata_devolucaoTEXTData e hora da devolução (NULL se em aberto)


Instalação e Uso

Pré-requisitos

bashpip install reportlab python-barcode pillow matplotlib

Execução

bashpython cautelas.py

Distribuição (executável Windows)

bashpyinstaller --onefile --windowed --icon=icone.ico cautelas.py


O executável gerado em dist/ pode ser distribuído sem dependência de instalação Python no destino.




Observações Técnicas


O banco de dados banco_de_dados.db é criado automaticamente na primeira execução
PDFs gerados são salvos em cautelas/ e abertos automaticamente após emissão
Imagens de código de barras são salvas em codigos/ e referenciadas no PDF
A coluna codigo_cautela foi adicionada via ALTER TABLE para manter compatibilidade com bancos existentes
Caminhos de saída utilizam os.makedirs(..., exist_ok=True) para criação segura de diretórios



Licença

Projeto de uso institucional. Desenvolvido para fins de portfólio e aprendizado.
