#!/usr/bin/env python3
"""
CommitIA - Ferramenta CLI para gerar mensagens de commit automáticas
usando CrewAI e seguindo o padrão Conventional Commits
"""

import os
import sys
import click
import git
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool


def get_llm():
    """Configura e retorna o modelo LLM do Google (Gemini)"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        click.echo(
            "GOOGLE_API_KEY não encontrada. Configure sua chave da API do Google AI Studio.",
            err=True,
        )
        click.echo("    Obtenha sua chave em: https://aistudio.google.com/", err=True)
        sys.exit(1)

    return LLM(model="gemini/gemini-2.0-flash-lite", temperature=0.3, api_key=api_key)


@dataclass
class GitChange:
    """Representa uma mudança no Git"""

    file_path: str
    change_type: str  # A (added), M (modified), D (deleted), R (renamed)
    lines_added: int
    lines_removed: int
    diff_content: str


class GitAnalyzer:
    """Classe para analisar mudanças no repositório Git"""

    def __init__(self, repo_path: str = "."):
        try:
            self.repo = git.Repo(repo_path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            click.echo(
                f"❌ Erro: '{repo_path}' não é um repositório Git válido.", err=True
            )
            sys.exit(1)

    def has_staged_changes(self) -> bool:
        """Verifica se há mudanças staged, tratando o caso de um repositório novo."""
        try:
            # Tenta acessar o commit do HEAD. Lança ValueError em repo vazio.
            self.repo.head.commit
            # Se não houver erro, o repositório tem commits. Usa a lógica padrão.
            return len(self.repo.index.diff("HEAD")) > 0
        except ValueError:
            # Se ValueError foi lançado, o repo está vazio.
            # Nesse caso, verificamos se o index (área de stage) tem alguma entrada.
            return len(self.repo.index.entries) > 0

    def has_unstaged_changes(self) -> bool:
        """Verifica se há mudanças não staged"""
        return len(self.repo.index.diff(None)) > 0

    def get_staged_changes(self) -> List[GitChange]:
        """Obtém as mudanças staged, tratando o caso de um repositório novo."""
        changes = []
        try:
            # Tenta acessar o commit do HEAD para ver se o repo não está vazio.
            self.repo.head.commit
            diffs = self.repo.index.diff("HEAD")
        except ValueError:
            # Se o repo está vazio, todos os arquivos no index são 'Added'.
            # Iteramos sobre as entradas do index em vez de fazer um diff.
            for path, entry in self.repo.index.entries.items():
                stream = self.repo.odb.stream(entry.binsha)
                content = stream.read().decode("utf-8", errors="ignore")

                lines_added = content.count("\n")
                if content:
                    lines_added += 1

                change = GitChange(
                    file_path=path,
                    change_type="A",
                    lines_added=lines_added,
                    lines_removed=0,
                    diff_content=f"--- /dev/null\n+++ b/{path}\n"
                    + "\n".join(f"+{line}" for line in content.splitlines()),
                )

                changes.append(change)
            return changes

        # Lógica original para repositórios com commits.
        for diff in diffs:
            change = GitChange(
                file_path=diff.a_path or diff.b_path,
                change_type=diff.change_type,
                lines_added=0,
                lines_removed=0,
                diff_content="",
            )

            if diff.diff:
                change.diff_content = diff.diff.decode("utf-8", errors="ignore")
                for line in change.diff_content.split("\n"):
                    if line.startswith("+") and not line.startswith("+++"):
                        change.lines_added += 1
                    elif line.startswith("-") and not line.startswith("---"):
                        change.lines_removed += 1

            changes.append(change)

        return changes

    def get_recent_commits(self, count: int = 5) -> List[str]:
        """Obtém mensagens dos commits recentes para contexto."""
        try:
            # Tenta acessar o commit do HEAD para ver se o repo não está vazio.
            self.repo.head.commit
            commits = list(self.repo.iter_commits(max_count=count))
            return [commit.message.strip() for commit in commits]
        except ValueError:
            # Se não houver commits, retorna uma lista vazia.
            return []


class GitAnalysisTool(BaseTool):
    """Tool para análise de mudanças do Git"""

    name: str = "git_analysis"
    description: str = (
        "Analisa mudanças no repositório Git e extrai informações relevantes"
    )

    git_analyzer: GitAnalyzer = None

    def __init__(self, git_analyzer: GitAnalyzer):
        super().__init__()
        self.git_analyzer = git_analyzer

    def _run(self) -> str:
        """Executa a análise do Git"""
        changes = self.git_analyzer.get_staged_changes()
        recent_commits = self.git_analyzer.get_recent_commits()

        if not changes:
            return "Nenhuma mudança staged encontrada."

        analysis = {
            "total_files": len(changes),
            "files_by_type": {},
            "changes_summary": [],
            "recent_commits": recent_commits[:3],  # Últimos 3 commits para contexto
        }

        for change in changes:
            # Agrupar por tipo de mudança
            change_type_desc = {
                "A": "adicionados",
                "M": "modificados",
                "D": "deletados",
                "R": "renomeados",
            }

            type_desc = change_type_desc.get(change.change_type, "modificados")
            if type_desc not in analysis["files_by_type"]:
                analysis["files_by_type"][type_desc] = []

            analysis["files_by_type"][type_desc].append(
                {
                    "file": change.file_path,
                    "lines_added": change.lines_added,
                    "lines_removed": change.lines_removed,
                }
            )

            # Resumo das mudanças
            summary = f"{change.file_path} ({type_desc})"
            if change.lines_added > 0 or change.lines_removed > 0:
                summary += f" - +{change.lines_added}/-{change.lines_removed} linhas"

            analysis["changes_summary"].append(summary)

        return str(analysis)


def create_agents_and_tasks(
    git_analyzer: GitAnalyzer,
) -> Tuple[List[Agent], List[Task]]:
    """Cria os agentes e tarefas do CrewAI"""

    llm = get_llm()
    git_tool = GitAnalysisTool(git_analyzer)

    # Agente Analista de Código
    code_analyst = Agent(
        role="Analista de Código Git",
        goal="Analisar mudanças no código e identificar o tipo e escopo das modificações",
        backstory="""Você é um especialista em análise de código que entende diferentes 
        linguagens de programação e padrões de desenvolvimento. Sua função é analisar 
        as mudanças no Git e classificá-las adequadamente.""",
        tools=[git_tool],
        llm=llm,
        verbose=True,
    )

    # Agente Especialista em Conventional Commits
    commit_specialist = Agent(
        role="Especialista em Conventional Commits",
        goal="Gerar mensagens de commit seguindo rigorosamente o padrão Conventional Commits",
        backstory="""Você é um especialista no padrão Conventional Commits e conhece 
        profundamente as convenções de:
        - feat: novas funcionalidades
        - fix: correção de bugs
        - docs: documentação
        - style: formatação, ponto e vírgula, etc
        - refactor: refatoração que não adiciona funcionalidade nem corrige bugs
        - test: adição de testes
        - chore: mudanças no build, ferramentas auxiliares, etc
        - perf: melhorias de performance
        - ci: mudanças na configuração de CI/CD
        - build: mudanças no sistema de build
        - revert: reversão de commits anteriores""",
        llm=llm,
        verbose=True,
    )

    # Tarefa de Análise
    analysis_task = Task(
        description="""Analise as mudanças staged no repositório Git usando a ferramenta 
        git_analysis. Identifique:
        1. Quais arquivos foram modificados
        2. Tipo de mudanças (adição, modificação, remoção)
        3. Extensões dos arquivos e linguagens envolvidas
        4. Padrões nas mudanças (são testes? documentação? código de produção?)
        5. Contexto baseado nos commits recentes
        
        Forneça uma análise detalhada e estruturada.""",
        agent=code_analyst,
        expected_output="Análise detalhada das mudanças no repositório com classificação por tipo e contexto",
    )

    # Tarefa de Geração de Commit
    commit_generation_task = Task(
        description="""Com base na análise das mudanças, gere uma mensagem de commit 
        seguindo RIGOROSAMENTE o padrão Conventional Commits:
        
        Formato: <tipo>(<escopo opcional>): <descrição>
        
        Regras:
        - Use apenas tipos válidos: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert
        - Descrição deve ser concisa (máximo 50 caracteres no título)
        - Use imperativo ("add" não "added")
        - Sem ponto final no título
        - Se necessário, adicione corpo explicativo
        - Para breaking changes, adicione "!" após o escopo
        
        Exemplos:
        - feat(auth): add user login functionality
        - fix(api): resolve null pointer exception in user service
        - docs: update installation instructions
        - refactor(utils): simplify date formatting logic
        
        Retorne APENAS a mensagem de commit, sem explicações adicionais.""",
        agent=commit_specialist,
        expected_output="Mensagem de commit formatada segundo Conventional Commits",
        context=[analysis_task],
    )

    return [code_analyst, commit_specialist], [analysis_task, commit_generation_task]


@click.group()
def cli():
    """CommitIA - Gerador automático de mensagens de commit"""
    pass


@cli.command()
@click.option(
    "--auto-commit",
    "-c",
    is_flag=True,
    help="Fazer commit automaticamente após gerar a mensagem",
)
@click.option("--verbose", "-v", is_flag=True, help="Mostrar saída detalhada")
@click.option("--repo-path", "-r", default=".", help="Caminho para o repositório Git")
def generate(auto_commit: bool, verbose: bool, repo_path: str):
    """Gera mensagem de commit usando IA"""

    click.echo("Analisando repositório Git...")

    # Inicializar analisador Git
    git_analyzer = GitAnalyzer(repo_path)

    # Verificar se há mudanças staged
    if not git_analyzer.has_staged_changes():
        if git_analyzer.has_unstaged_changes():
            click.echo("⚠️  Há mudanças não staged. Execute 'git add' primeiro.")
        else:
            click.echo("ℹ️  Nenhuma mudança encontrada para commit.")
        return

    # Criar agentes e tarefas
    agents, tasks = create_agents_and_tasks(git_analyzer)

    # Configurar e executar crew
    crew = Crew(agents=agents, tasks=tasks, process=Process.sequential, verbose=verbose)

    click.echo("Gerando mensagem de commit com IA...")

    try:
        # Executar o crew
        result = crew.kickoff()

        # Extrair mensagem de commit do resultado
        commit_message = str(result).strip()

        click.echo("\n" + "=" * 60)
        click.echo("MENSAGEM DE COMMIT GERADA:")
        click.echo("=" * 60)
        click.echo(commit_message)
        click.echo("=" * 60 + "\n")

        if auto_commit:
            # Fazer commit automaticamente
            git_analyzer.repo.index.commit(commit_message)
            click.echo("Commit realizado com sucesso!")
        else:
            # Perguntar se o usuário quer fazer o commit
            if click.confirm("Deseja fazer o commit com esta mensagem?"):
                git_analyzer.repo.index.commit(commit_message)
                click.echo("Commit realizado com sucesso!")
            else:
                click.echo(
                    "Mensagem salva. Use 'git commit -m \"{}\"' para fazer o commit manualmente.".format(
                        commit_message
                    )
                )

    except Exception as e:
        click.echo(f"Erro ao gerar commit: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--repo-path", "-r", default=".", help="Caminho para o repositório Git")
def status(repo_path: str):
    """Mostra o status do repositório"""

    git_analyzer = GitAnalyzer(repo_path)

    click.echo("STATUS DO REPOSITÓRIO:")
    click.echo("-" * 40)

    # Mudanças staged
    staged_changes = git_analyzer.get_staged_changes()
    if staged_changes:
        click.echo(f"Mudanças staged: {len(staged_changes)} arquivo(s)")
        for change in staged_changes:
            click.echo(f"   {change.file_path} ({change.change_type})")
    else:
        click.echo("Nenhuma mudança staged")

    # Mudanças não staged
    if git_analyzer.has_unstaged_changes():
        click.echo("Há mudanças não staged")

    # Commits recentes
    recent_commits = git_analyzer.get_recent_commits(3)
    if recent_commits:
        click.echo("\nÚltimos commits:")
        for i, commit in enumerate(recent_commits, 1):
            click.echo(f"   {i}. {commit[:60]}...")


@cli.command()
def setup():
    """Configura a ferramenta (verifica dependências)"""

    click.echo("Verificando configuração...")

    # Verificar se está em um repositório Git
    try:
        git.Repo(".")
        click.echo("Repositório Git encontrado")
    except git.InvalidGitRepositoryError:
        click.echo("Não está em um repositório Git")
        return

    # Verificar chave da API OpenAI
    if os.getenv("GOOGLE_API_KEY"):
        click.echo("GOOGLE_API_KEY configurada")
    else:
        click.echo("GOOGLE_API_KEY não encontrada")
        click.echo("   Configure com: export GOOGLE_API_KEY='sua-chave-aqui'")
        return

    click.echo("Configuração OK! Use 'commitia generate' para começar.")


if __name__ == "__main__":
    cli()
