
STRUCTURE_CONTENT = """
## 📂 Estrutura do Projeto

Abaixo, um esquema dos principais diretórios e arquivos do projeto:

```
AgenteNoticiasSegPub/
├── app.py                # 🖥️ Frontend (Streamlit) - Interface do usuário e lógica de exibição.
├── auth_config.yaml      # 🔐 Configurações de Autenticação (Usuários e Cookies). IGNORADO no Git.
├── .env                  # 🔑 Variáveis de Ambiente (API Keys). IGNORADO no Git.
├── docker-compose.yml    # 🐳 Orquestração de Containers (Frontend, Backend, Redis).
├── requirements.txt      # 📦 Dependências Python do projeto.
│
├── backend/              # 🧠 Lógica do Servidor (API FastAPI)
│   ├── main.py           # Ponto de entrada da API, rotas /news, /chat e agendador.
│   ├── agent.py          # Lógica de Inteligência Artificial (Groq/Gemini).
│   ├── fetchers.py       # Coletores de Notícias (Google RSS, NewsAPI, DuckDuckGo).
│   ├── database.py       # Conexão com Banco de Dados (SQLite/Async).
│   ├── models.py         # Modelos de Dados (Pydantic/SQLAlchemy).
│   ├── logging_config.py # Configuração de Logs Estruturados.
│   └── utils.py          # Funções utilitárias (Data, validações).
│
├── data/                 # 💾 Armazenamento Persistente
│   └── noticias.db       # Banco de Dados SQLite (Notícias e Logs).
│
└── .github/              # ⚙️ Automação (DevOps)
    └── workflows/ci.yml  # Pipeline de Integração Contínua (Testes e Lint).
```
"""

AUTH_CONTENT = """
## 🔐 Controle de Acesso e Usuários

Para garantir a segurança do painel administrativo, implementamos um sistema de autenticação robusto.

### Arquitetura de Autenticação (Opção 1 - Ágil)
Optamos pela arquitetura **Streamlit Authenticator** (baseada em cookies cifrados e configuração local) em detrimento de uma solução complexa baseada em JWT/Banco de Dados. 

**Justificativa:**
- **Agilidade**: Permitiu implementação imediata sem necessidade de migração de banco de dados.
- **Suficiência**: Adequada para o cenário atual de uso interno por equipe restrita.
- **Segurança**: As senhas são armazenadas apenas como **Hashes** seguras (bcrypt), nunca em texto plano.

### ⚠️ Aviso de Segurança
**NUNCA** commite o arquivo `auth_config.yaml` com senhas reais. Ele deve ser configurado apenas no ambiente de produção.

### Como Gerenciar Usuários
1.  Utilize o script utilitário para gerar hashes de senha seguras:
    ```bash
    python generate_keys.py
    ```
2.  Copie as hashes geradas para o arquivo `auth_config.yaml`.
3.  Reinicie a aplicação para aplicar as alterações.
"""

import codecs

def update_readme():
    try:
        # Tentar ler com utf-16 (encoding atual provável)
        try:
            with codecs.open('README.md', 'r', 'utf-16') as f:
                content = f.read()
        except:
            # Fallback para utf-8
            with codecs.open('README.md', 'r', 'utf-8') as f:
                content = f.read()

        # 1. Remover a seção antiga de Auth se existir (baseada no titulo)
        if "##  User Access Control (Novo)" in content:
            parts = content.split("##  User Access Control (Novo)")
            # Manter a parte antes, descartar a parte depois (assumindo que estava no final)
            # Mas cuidado, se tiver algo depois. O usuário disse que estava no final.
            # Vamos ser mais cirurgicos.
            pre_auth = parts[0]
            # O resto pode conter "---" ou fim de arquivo.
            # O user disse que adicionou no final.
            content = pre_auth.strip()

        # 2. Inserir Auth Content ANTES de "## 🏆 Desafios Solucionados"
        marker = "## 🏆 Desafios Solucionados"
        if marker in content:
            content = content.replace(marker, AUTH_CONTENT + "\n\n" + marker)
        else:
            # Se não achar o marker, avisa mas anexa no final (fallback)
            print("AVISO: Marcador 'Desafios Solucionados' não encontrado. Anexando Auth no início.")
            content = AUTH_CONTENT + "\n\n" + content

        # 3. Anexar Estrutura no final
        content = content + "\n\n" + STRUCTURE_CONTENT

        # 4. Salvar (vamos salvar em UTF-8 para padronizar daqui pra frente)
        with codecs.open('README.md', 'w', 'utf-8') as f:
            f.write(content)
        
        print("README atualizado com sucesso!")

    except Exception as e:
        print(f"Erro ao atualizar README: {e}")

if __name__ == "__main__":
    update_readme()
