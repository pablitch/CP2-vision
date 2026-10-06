# CP2 — MVP de Visão Computacional para a Inova Trônica

Aplicação em Python e Streamlit que envia uma imagem ao Azure AI Vision e apresenta a descrição, o nível de confiança e as etiquetas (tags), conforme o documento `CP2.docx`.

## Identificação

| Campo | Informação |
|---|---|
| Instituição | FIAP |
| Curso | Engenharia Mecatrônica |
| Disciplina | Cloud Computing & Machine as a Service (MaaS) |
| Integrante | Pablo Monte — RM 96322 |
| Integrante | Murilo Henrique Costa — RM 96203 |
| Turma | 5EMR |
| Ano | 2026 |

## Funcionalidades

- Carregamento de imagem local em JPG, JPEG, PNG ou BMP.
- Análise por URL pública direta da imagem.
- API Analyze v3.2: descrição e tags em português, selecionada por padrão.
- API Image Analysis 4.0: descrição e tags em inglês.
- Exibição do nível de confiança e da resposta JSON da API.
- Credenciais em `.env` ou variáveis de ambiente, sem chave no código.
- Mensagens para falhas de autenticação, conexão, tempo de resposta e limite de requisições.

## Recurso Azure utilizado no documento

O relatório registra um recurso Computer Vision com os seguintes dados:

| Campo | Valor registrado |
|---|---|
| Nome do recurso | `visao-inova-rm96322` |
| Região | East US |
| Camada | Free (F0) |

A aplicação usa esse recurso existente; ela não cria nem altera recursos na Azure. A geração de legendas pela API 4.0 depende da disponibilidade regional. Caso o serviço recuse esse recurso, selecione a API v3.2.

**Copie o endpoint diretamente do portal.** O nome do endpoint pode ser diferente do nome exibido para o recurso; não substitua o RM dentro do endereço. Nome e RM do aluno estão na identificação da aplicação, enquanto o endpoint precisa continuar sendo o endereço real do serviço.

## Como executar no Windows (PowerShell)

É necessário ter Python 3.10 ou superior. Abra o PowerShell na pasta que contém `app.py` e execute:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

No portal Azure, abra o recurso **Computer Vision → Chaves e ponto de extremidade**. No `.env`, preencha `AZURE_VISION_ENDPOINT` com o endpoint HTTPS completo e `AZURE_VISION_KEY` com uma das chaves do mesmo recurso. Salve o arquivo e execute:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra o endereço mostrado no terminal, normalmente `http://localhost:8501`. Esses comandos utilizam o Python do ambiente virtual diretamente, sem precisar ativar scripts no PowerShell.

Se alterar o `.env` com a aplicação aberta, pare com `Ctrl+C` e execute novamente. Variáveis de ambiente que já existam no sistema têm prioridade sobre o arquivo `.env`.

### Linux/macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
# Edite o .env e preencha as credenciais antes de iniciar.
.venv/bin/python -m streamlit run app.py
```

## Como usar

1. Confirme a mensagem **Credenciais configuradas** na lateral. Essa mensagem indica que os campos foram preenchidos; a validade da chave será verificada na primeira análise.
2. Mantenha **v3.2 (descrição em português)** para reproduzir o fluxo mostrado no documento.
3. Escolha **Arquivo local** e carregue uma imagem, ou selecione **URL** e informe um link direto e público.
4. Clique em **Analisar imagem**.
5. Confira a descrição, a confiança e as tags. O expansor mostra a resposta completa retornada pela Azure.

O processamento acontece na Azure e requer internet. Não há resultados pré-gravados na aplicação. As imagens são enviadas ao serviço apenas ao clicar em **Analisar imagem**; a pré-visualização de uma URL pode acessar o endereço informado antes disso.

## Publicar no seu GitHub e colocar o link no documento

1. Extraia o ZIP e abra a pasta do projeto.
2. No GitHub, crie um repositório, por exemplo `CP2-Azure-AI-Vision`.
3. Use **Add file → Upload files** e envie os arquivos do projeto, mantendo a pasta `tests`.
4. Inclua `.env.example` e `.gitignore`. **Não envie `.env`, `.venv` ou chaves reais.** Ao fazer upload pelo navegador, o `.gitignore` não impede o envio de um arquivo selecionado manualmente.
5. Clique em **Commit changes**.
6. Copie a URL real do repositório criado e cole na seção **Link do código** do `CP2.docx`.

O link do GitHub permite consultar e baixar o código. Ele não executa o aplicativo Streamlit. O documento continua separado do código; o link final depende do repositório que você criar.

## Arquivos

| Arquivo | Finalidade |
|---|---|
| `app.py` | Interface Streamlit e chamadas REST ao Azure AI Vision |
| `requirements.txt` | Dependências da aplicação |
| `.env.example` | Modelo sem credenciais para criar o `.env` |
| `.gitignore` | Exclusão de credenciais e arquivos locais do controle de versão |
| `tests/test_app.py` | Verificação local das requisições, respostas e interface |
| `README.md` | Identificação, configuração e instruções de execução |

## Validação local

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes utilizam respostas simuladas para verificar a montagem das requisições, a leitura dos resultados e o comportamento da interface. Não consomem a API nem comprovam o acesso ao seu recurso Azure. A validação real deve ser feita executando a aplicação com suas credenciais e uma imagem.

## Origem e referências

Adaptação do projeto [M4ns0urX/Azure-AI-Vision](https://github.com/M4ns0urX/Azure-AI-Vision). A base das chamadas REST e do fluxo da interface foi preservada. Esta versão personaliza a identificação para o CP2, inclui o modelo `.env.example`, ajusta as dependências e acrescenta validações e instruções de execução.

- [Microsoft — Chamar a API Image Analysis 4.0](https://learn.microsoft.com/pt-br/azure/ai-services/computer-vision/how-to/call-analyze-image-40)
- [Microsoft — Legendas de imagem 4.0](https://learn.microsoft.com/pt-br/azure/ai-services/computer-vision/concept-describe-images-40)
- [Streamlit — Exibição de imagens](https://docs.streamlit.io/develop/api-reference/media/st.image)
- [Streamlit — Testes com AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest)
