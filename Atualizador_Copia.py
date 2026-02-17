import os
import sys
from datetime import datetime
from git import Repo, GitCommandError

# =========================
# CONFIGURAÇÃO
# =========================
CAMINHO_PROJETO = r"C:\Python\Dashboard_Sauipe"
MENSAGEM_PREFIXO = "Atualização automática dashboard"

# Se você quiser forçar inclusão de arquivos em pasta ignorada, coloque aqui:
# Ex.: ["dados/*.csv", "dados/*.xlsx"]
FORCAR_INCLUSAO_PADROES = []


def print_secao(titulo: str):
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)


def listar_estado_repo(repo: Repo):
    """Mostra diagnóstico completo do estado do repositório."""
    print_secao("🔎 Diagnóstico do repositório")
    branch = repo.active_branch.name if not repo.head.is_detached else "(detached HEAD)"
    print(f"Branch atual: {branch}")

    changed = [item.a_path for item in repo.index.diff(None)]  # tracked modificados
    staged = [item.a_path for item in repo.index.diff("HEAD")] if repo.head.is_valid() else []
    untracked = list(repo.untracked_files)

    print(f"Arquivos modificados (tracked, não staged): {len(changed)}")
    for f in changed:
        print(f"  M  {f}")

    print(f"Arquivos staged: {len(staged)}")
    for f in staged:
        print(f"  A/M {f}")

    print(f"Arquivos untracked: {len(untracked)}")
    for f in untracked:
        print(f"  ?? {f}")

    return changed, staged, untracked


def arquivos_ignorados(repo: Repo, paths):
    """Retorna quais paths estão sendo ignorados pelo .gitignore."""
    ignorados = []
    for p in paths:
        try:
            # check-ignore retorna 0 quando é ignorado
            repo.git.check_ignore(p)
            ignorados.append(p)
        except GitCommandError:
            # não ignorado
            pass
    return ignorados


def atualizar_projeto():
    try:
        print_secao("🚀 Iniciando atualização")
        print(f"Repositório: {CAMINHO_PROJETO}")

        repo = Repo(CAMINHO_PROJETO)
        if repo.bare:
            raise RuntimeError("Repositório inválido (bare).")

        origin = repo.remote("origin")
        branch = repo.active_branch.name if not repo.head.is_detached else "main"

        # 1) Diagnóstico inicial
        changed, staged, untracked = listar_estado_repo(repo)

        # 2) Detecta se arquivos novos estão ignorados
        if untracked:
            ignorados = arquivos_ignorados(repo, untracked)
            if ignorados:
                print_secao("⚠️ Arquivos ignorados detectados (.gitignore)")
                for f in ignorados:
                    print(f"  IGNORED: {f}")
                print("\nEsses arquivos NÃO entram com git add -A.")
                print("Ajuste seu .gitignore ou use forçar inclusão (git add -f).")

        # 3) Adiciona tudo que não for ignorado
        print_secao("📂 Stage de alterações")
        repo.git.add(A=True)

        # 3.1) Forçar inclusão (opcional)
        for padrao in FORCAR_INCLUSAO_PADROES:
            try:
                repo.git.add("-f", padrao)
                print(f"Forçado inclusão: {padrao}")
            except Exception as e:
                print(f"Não foi possível forçar {padrao}: {e}")

        # 4) Se não houver nada staged, encerrar
        has_head = repo.head.is_valid()
        staged_after = [item.a_path for item in repo.index.diff("HEAD")] if has_head else []
        if has_head and not staged_after:
            print("\n✅ Nenhuma alteração para commit (após stage).")
            return

        # 5) Commit
        data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
        mensagem = f"{MENSAGEM_PREFIXO} - {data_hoje}"
        repo.index.commit(mensagem)
        print(f"📝 Commit criado: {mensagem}")

        # 6) Atualiza remoto com rebase (evita merge commit automático)
        print_secao("⬇️ Sincronizando com remoto (pull --rebase)")
        try:
            repo.git.pull("--rebase", "origin", branch)
            print("✅ Pull com rebase concluído.")
        except Exception as e:
            print(f"⚠️ Pull com rebase falhou: {e}")
            print("Tentando push mesmo assim...")

        # 7) Push para branch atual
        print_secao("⬆️ Push para GitHub")
        push_info = origin.push(refspec=f"{branch}:{branch}")
        for info in push_info:
            print(str(info))

        print("\n✅ SUCESSO: atualização enviada. Aguarde o deploy do Streamlit Cloud.")

    except Exception as e:
        print_secao("❌ ERRO CRÍTICO")
        print(e)
        print("\nChecklist rápido:")
        print("1) Verifique se CAMINHO_PROJETO está correto")
        print("2) Rode: git status")
        print("3) Verifique .gitignore para pasta 'dados'")
        print("4) Confirme branch: git branch --show-current")
        print("5) Se necessário: git pull --rebase origin main")
        sys.exit(1)


if __name__ == "__main__":
    atualizar_projeto()
    input("\nPressione Enter para sair...")
