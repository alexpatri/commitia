# README.md

# 🚀 Git Commit AI

Uma ferramenta de linha de comando inteligente que gera mensagens de commit automáticas seguindo o padrão **Conventional Commits** usando IA (CrewAI + Gemini).

## ✨ Funcionalidades

- 🤖 **Geração automática** de mensagens de commit usando IA
- 📋 **Conventional Commits** - Segue rigorosamente o padrão
- 🔍 **Análise inteligente** do diff do Git
- 👥 **Multi-agente** - Usa CrewAI com agentes especializados
- 🎯 **Classificação precisa** - Identifica feat, fix, docs, refactor, etc.
- ⚡ **Interface simples** - CLI fácil de usar
- 🔧 **Configurável** - Suporte a diferentes repositórios

## 🛠️ Instalação

### Pré-requisitos

- Python 3.8+
- Git
- Chave da API OpenAI

### Instalação via pip

```bash
pip install commitia
```

### Instalação para desenvolvimento

```bash
git clone https://github.com/alexpatri/commitia.git
cd commitia
pip install -e .
```

## ⚙️ Configuração

1. **Configure sua chave da API Google:**

```bash
export GOOGLE_API_KEY="sua-chave-da-api"
```

2. **Verifique a configuração:**

```bash
commitia setup
```

## 🚀 Uso

### Comandos disponíveis

```bash
# Gerar mensagem de commit
commitia generate

# Gerar e fazer commit automaticamente
commitia generate --auto-commit

# Ver status do repositório
commitia status

# Verificar configuração
commitia setup

# Ajuda
commitia --help
```

### Fluxo típico de uso

```bash
# 1. Fazer mudanças no código
echo "nova funcionalidade" >> arquivo.py

# 2. Adicionar ao staging
git add arquivo.py

# 3. Gerar commit com IA
commitia generate

# Resultado: feat: add new functionality to arquivo.py
```

### Exemplos de saída

A ferramenta gera mensagens seguindo o padrão Conventional Commits:

```
feat(auth): add JWT token validation
fix(api): resolve memory leak in user service
docs: update installation guide
refactor(utils): simplify date formatting logic
test(auth): add unit tests for login flow
chore(deps): update dependencies to latest versions
```

## 🧠 Como Funciona

A ferramenta usa uma arquitetura multi-agente com **CrewAI**:

### Agentes

1. **Analista de Código Git** 🔍

   - Analisa mudanças no repositório
   - Identifica tipos de arquivo e modificações
   - Extrai contexto dos commits recentes

2. **Especialista em Conventional Commits** 📝
   - Especializado no padrão Conventional Commits
   - Gera mensagens precisas e bem formatadas
   - Garante conformidade com as convenções

### Processo

```
Mudanças Staged → Análise Git → Classificação → Geração de Mensagem → Commit
```

## 📋 Tipos de Commit Suportados

| Tipo       | Descrição           | Exemplo                           |
| ---------- | ------------------- | --------------------------------- |
| `feat`     | Nova funcionalidade | `feat(auth): add login system`    |
| `fix`      | Correção de bug     | `fix(api): resolve null pointer`  |
| `docs`     | Documentação        | `docs: update README`             |
| `style`    | Formatação          | `style: fix indentation`          |
| `refactor` | Refatoração         | `refactor: simplify user logic`   |
| `test`     | Testes              | `test: add user validation tests` |
| `chore`    | Manutenção          | `chore: update dependencies`      |
| `perf`     | Performance         | `perf: optimize database queries` |
| `ci`       | CI/CD               | `ci: add GitHub Actions workflow` |
| `build`    | Build system        | `build: update webpack config`    |
| `revert`   | Reversão            | `revert: undo previous commit`    |

## 🔧 Opções Avançadas

### Configuração por projeto

Crie um arquivo `.env` no seu projeto:

```env
GOOGLE_API_KEY=sua-chave-aqui
```

### Personalização de prompts

A ferramenta permite personalizar o comportamento dos agentes modificando seus `backstory` e `goal`.

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'feat: add amazing feature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

## 🆘 Suporte

- 📖 [Documentação](https://github.com/alexpatri/commitia/wiki)
- 🐛 [Issues](https://github.com/alexpatri/commitia/issues)
- 💬 [Discussões](https://github.com/alexpatri/commitia/discussions)

## 🎯 Roadmap

- [ ] Suporte a outros providers de LLM (Claude, OpenAI)
- [ ] Configuração de templates personalizados
- [ ] Integração com hooks do Git
- [ ] Interface gráfica opcional
- [ ] Suporte a diferentes idiomas
- [ ] Cache de análises para repositórios grandes
