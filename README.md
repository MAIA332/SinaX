# SinaX - Sistema RAG Multi-Provedor com Cache

SinaX é um poderoso sistema RAG (Retrieval-Augmented Generation) que suporta múltiplos provedores de LLM e fontes de dados, com um sistema inteligente de cache de perguntas e respostas.

## Arquitetura do Sistema

### Componentes Principais

1. **Integração com LLM**
   - Suporte a múltiplos provedores (Groq, etc.)
   - Balanceamento de carga entre provedores
   - Seleção dinâmica de provedores

2. **Integração com Fontes de Dados**
   - Suporte a múltiplas fontes
   - Integração com banco de dados vetorial
   - Ingestão flexível de dados

3. **Sistema de Cache**
   - Cache baseado em Redis
   - Gerenciamento de metadados com PostgreSQL
   - Verificação de similaridade semântica

### Detalhes do Sistema de Cache

O sistema de cache foi projetado para otimizar tempos de resposta e reduzir chamadas à API de LLM, armazenando e recuperando perguntas e respostas similares.

#### Componentes

1. **Armazenamento Redis**
   - Armazena pares de pergunta-resposta em coleções
   - Mantém metadados sobre as coleções
   - Gerencia serialização/desserialização de dados

2. **Verificação de Similaridade**
   - Utiliza Sentence Transformers (all-MiniLM-L6-v2)
   - Implementa similaridade de cosseno para correspondência de perguntas
   - Limiar de similaridade configurável (padrão: 0.85)

3. **Gerenciamento de Metadados**
   - PostgreSQL armazena metadados das coleções
   - Rastreia tamanhos de coleções e contagem de registros
   - Mantém timestamps de criação e atualização

#### Fluxo do Cache

1. **Recepção da Pergunta**
   - Sistema recebe uma pergunta
   - Verifica cache por perguntas similares

2. **Verificação de Similaridade**
   - Calcula embeddings para a nova pergunta
   - Compara com perguntas em cache
   - Retorna resposta em cache se similaridade > limiar

3. **Atualização do Cache**
   - Se nenhuma pergunta similar for encontrada:
     - Processa pergunta com LLM
     - Armazena novo par QA no cache
     - Atualiza metadados

## Documentação da API

### Endpoints do Engine

#### POST /engine/completion
Processa uma pergunta usando o sistema de LLM com cache e balanceamento de carga. Esta rota é a principal para interação com o sistema, combinando cache, balanceamento de carga e gerenciamento de workspace.

**Corpo da Requisição:**
```json
{
    "question": "Qual é a capital da França?",
    "workspace_id": "opcional-uuid"  // Se não fornecido, um novo workspace será criado
}
```

**Resposta:**
```json
{
    "answer": "A capital da França é Paris.",
    "workspace_id": "uuid-do-workspace",
    "llm_provider": "groq",
    "cached": false,
    "similarity_score": null
}
```

**Comportamento:**
1. Verifica se a pergunta já foi respondida anteriormente (usando cache)
2. Se encontrada no cache, retorna a resposta com `cached: true`
3. Se não encontrada, seleciona o melhor provedor LLM usando balanceamento de carga
4. Processa a pergunta e armazena a resposta no cache
5. Atualiza o histórico do workspace
6. Retorna a resposta com detalhes do provedor usado

#### GET /engine/workspaces
Lista todos os workspaces e seus históricos de conversação. Cada workspace mantém um histórico completo de interações.

**Resposta:**
```json
{
    "message": "success",
    "content": [
        {
            "id": "uuid",
            "history": [
                {
                    "role": "user",
                    "content": "Qual é a capital da França?",
                    "timestamp": "2024-04-10T14:30:00"
                },
                {
                    "role": "assistant",
                    "content": "A capital da França é Paris.",
                    "timestamp": "2024-04-10T14:30:01"
                }
            ],
            "created_at": "2024-04-10T14:00:00",
            "updated_at": "2024-04-10T14:30:01"
        }
    ]
}
```

**Detalhes do Workspace:**
- Cada workspace possui um ID único
- Mantém histórico completo de interações
- Registra timestamps de criação e atualização
- Permite continuidade de conversas
- Suporta múltiplas sessões de conversa

#### POST /engine/workspaces
Cria um novo workspace vazio.

**Corpo da Requisição:**
```json
{
    "name": "Meu Workspace"  // opcional
}
```

**Resposta:**
```json
{
    "message": "success",
    "content": {
        "id": "uuid",
        "name": "Meu Workspace",
        "history": [],
        "created_at": "2024-04-10T14:00:00",
        "updated_at": "2024-04-10T14:00:00"
    }
}
```

#### GET /engine/workspaces/{workspace_id}
Obtém detalhes de um workspace específico.

**Resposta:**
```json
{
    "message": "success",
    "content": {
        "id": "uuid",
        "name": "Meu Workspace",
        "history": [
            {
                "role": "user",
                "content": "Qual é a capital da França?",
                "timestamp": "2024-04-10T14:30:00"
            },
            {
                "role": "assistant",
                "content": "A capital da França é Paris.",
                "timestamp": "2024-04-10T14:30:01"
            }
        ],
        "created_at": "2024-04-10T14:00:00",
        "updated_at": "2024-04-10T14:30:01"
    }
}
```

#### DELETE /engine/workspaces/{workspace_id}
Remove um workspace específico.

**Resposta:**
```json
{
    "message": "success",
    "content": {
        "id": "uuid",
        "deleted": true
    }
}
```

### Endpoints de Cache

#### GET /cache/
Recupera todas as coleções em cache.

**Resposta:**
```json
{
    "message": "success",
    "content": [
        {
            "id": "uuid",
            "name": "collection_name",
            "fields": ["field1", "field2"],
            "sizeInBytes": 1024,
            "createdAt": "timestamp",
            "updatedAt": "timestamp",
            "record_count": 10
        }
    ]
}
```

#### GET /cache/sync
Sincroniza coleções entre Redis e PostgreSQL.

**Resposta:**
```json
{
    "message": "success",
    "content": {
        "success": true,
        "message": "Coleções sincronizadas"
    }
}
```

#### POST /cache/qa
Armazena um novo par de pergunta-resposta em cache.

**Corpo da Requisição:**
```json
{
    "question": "Qual é a capital da França?",
    "answer": "A capital da França é Paris.",
    "llm_provider": "groq"
}
```

**Resposta:**
```json
{
    "message": "success",
    "content": {
        "id": "uuid"
    }
}
```

#### GET /cache/qa/{question}
Recupera perguntas similares em cache.

**Resposta:**
```json
{
    "message": "success",
    "content": {
        "question": "Qual é a capital da França?",
        "answer": "A capital da França é Paris.",
        "similarity_score": 0.95,
        "llm_provider": "groq",
        "created_at": "timestamp",
        "updated_at": "timestamp"
    },
    "cached": true
}
```

### Endpoints de Fonte

#### POST /source/execute
Executa um método em um plugin específico.

**Corpo da Requisição:**
```json
{
    "plugin_name": "groq",
    "method_name": "quest_something",
    "args": ["Qual é a capital da França?", "workspace_id"]
}
```

**Resposta:**
```json
{
    "message": "success",
    "content": "A capital da França é Paris.",
    "cached": false
}
```

## Configuração

### Variáveis de Ambiente

- `REDIS_HOST`: Host do servidor Redis (padrão: localhost)
- `REDIS_PORT`: Porta do servidor Redis (padrão: 6379)
- `REDIS_DB`: Número do banco de dados Redis (padrão: 0)
- `REDIS_PASSWORD`: Senha do Redis (opcional)
- `DATABASE_URL`: String de conexão PostgreSQL
- `SERVICES`: Caminho para o arquivo de configuração de serviços
- `GROQ_API_KEY`: Chave de API do Groq
- `QDRANT_HOST`: Host do servidor Qdrant
- `QDRANT_PORT`: Porta do servidor Qdrant
- `QDRANT_API_KEY`: Chave de API do Qdrant

### Configuração de Serviços

O arquivo de configuração de serviços define os provedores de LLM disponíveis e suas configurações:

```json
{
    "LLM": {
        "groq": {
            "habilited": true,
            "plugin_name": "Groq",
            "entry_point": "PyGroqImplementation"
        }
    },
    "VECTORS_DATABASE": {
        // Configurações do banco de dados vetorial
    }
}
```

## Instalação

1. Clone o repositório
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Visão Geral
Este sistema implementa um serviço de processamento de linguagem natural que utiliza múltiplos provedores de LLM (Large Language Models) com um sistema de cache inteligente. O sistema inclui balanceamento de carga entre diferentes provedores de LLM e um mecanismo de cache que evita processamento desnecessário de perguntas repetidas.

## Funcionalidades Principais

### Cache Inteligente
O sistema implementa um cache inteligente que:
- Armazena perguntas e respostas para evitar reprocessamento
- Utiliza coeficiente de similaridade para identificar perguntas similares
- Não armazena perguntas contextuais no cache

#### Perguntas Contextuais
O sistema identifica automaticamente perguntas que dependem do contexto da conversa e as processa diretamente com o LLM, sem usar o cache. Isso é feito através de uma lista de 30 palavras-chave que indicam dependência contextual:

```python
contextual_keywords = [
    "acabei de perguntar",
    "perguntei",
    "disse",
    "falei",
    "mencionei",
    "anteriormente",
    "antes",
    "última pergunta",
    "última mensagem",
    "histórico",
    "contexto",
    "conversa anterior",
    "diálogo anterior",
    "discussão anterior",
    "comentário anterior",
    "resposta anterior",
    "explicação anterior",
    "informação anterior",
    "dado anterior",
    "fato anterior",
    "referência anterior",
    "citado anteriormente",
    "mencionado antes",
    "falado antes",
    "dito antes",
    "comentado antes",
    "explicado antes",
    "respondido antes",
    "informado antes",
    "citado antes"
]
```

Exemplos de perguntas contextuais:
- "O que eu acabei de perguntar?"
- "Qual foi a última pergunta?"
- "O que eu disse antes?"
- "No contexto da nossa conversa..."
- "Como mencionei anteriormente..."
- "Na conversa anterior, você mencionou..."
- "Baseado no diálogo anterior..."
- "Em relação ao comentário anterior..."
- "Considerando a resposta anterior..."
- "Com base na explicação anterior..."

Quando uma pergunta contém qualquer uma dessas palavras-chave, o sistema:
1. Ignora o cache
2. Processa a pergunta diretamente com o LLM
3. Não armazena a resposta no cache
4. Mantém o histórico da conversa no workspace

### Workspaces
O sistema mantém workspaces separados para diferentes conversas, permitindo:
- Histórico de conversas independente
- Contexto específico para cada conversa
- Gerenciamento de múltiplas conversas simultâneas

### Balanceamento de Carga
O sistema implementa um balanceador de carga que:
- Distribui requisições entre diferentes provedores de LLM
- Considera métricas de saúde e desempenho
- Ajusta proporções de uso baseado em performance

## API Endpoints

### Engine
- **POST /engine/completion**
  - Processa uma pergunta usando o sistema de LLM com cache e balanceamento de carga
  - Request body:
    ```json
    {
        "question": "Qual é a capital da França?",
        "workspace_id": "optional-uuid"
    }
    ```
  - Response:
    ```json
    {
        "answer": "A capital da França é Paris...",
        "workspace_id": "uuid",
        "llm_provider": "Groq",
        "cached": false,
        "similarity_score": null
    }
    ```

- **GET /engine/workspaces**
  - Lista todos os workspaces e seus históricos de conversa
  - Response:
    ```json
    {
        "message": "success",
        "content": [
            {
                "id": "uuid",
                "history": [
                    {
                        "role": "user",
                        "content": "Qual é a capital da França?",
                        "timestamp": "2025-04-10 12:15:36.609056"
                    },
                    {
                        "role": "assistant",
                        "content": "A capital da França é Paris...",
                        "timestamp": "2025-04-10 12:15:36.609063"
                    }
                ],
                "created_at": "2025-04-10 12:15:36.609056",
                "updated_at": "2025-04-10 12:15:36.609063"
            }
        ]
    }
    ```

### Cache
- **GET /cache/view**
  - Visualiza todo o cache da aplicação
  - Response:
    ```json
    {
        "message": "success",
        "content": {
            "qa_cache": [...],
            "workspaces": [...],
            "collections": {...},
            "metadata": {...}
        }
    }
    ```

- **DELETE /cache/clear**
  - Limpa todo o cache da aplicação
  - Response:
    ```json
    {
        "message": "success",
        "content": {
            "qa_cache_cleared": true,
            "workspaces_cleared": true,
            "metadata_cleared": true,
            "cleared": true
        }
    }
    ```

## Configuração

### Variáveis de Ambiente
```env
APP_NAME=SinaX
SERVICES=./services.json
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
GROQ_API_KEY=
```

### Dependências
- Python 3.8+
- Redis
- PostgreSQL
- Qdrant
- Groq
- FastAPI
- python-dotenv
- prisma
- redis-py
- groq

## Performance
- Cache de perguntas e respostas para reduzir latência
- Balanceamento de carga entre provedores de LLM
- Workspaces para manter contexto de conversas
- Identificação automática de perguntas contextuais