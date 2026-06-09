import sys
import os
import shutil

REPO_URL = "https://github.com/SEU_USUARIO/AgenteFO.git"  # substitua pelo seu repo

JOKES = [
    "🧵 Preparando os fios de ouro...",
    "👙 Organizando o estoque virtual...",
    "📋 Verificando as regras de negócio...",
    "🏦 Consultando o cadastro de representantes...",
    "✨ Quase lá, polindo os detalhes...",
]

_joke_index = 0

def next_joke():
    global _joke_index
    joke = JOKES[_joke_index % len(JOKES)]
    _joke_index += 1
    return joke


def ensure_in_colab():
    try:
        import google.colab
        return True
    except ImportError:
        return False


def setup_auth_first():
    print("  🔐 Solicitando permissões do Google Drive")
    print("-" * 60)
    print("\n📋 Preciso dessa permissão para acessar sua planilha de representantes no Drive...\n")

    try:
        from google.colab import drive, auth
        from googleapiclient.discovery import build
        import os
    except ImportError:
        print("⚠️  Não está no Colab. Pulando autenticação.")
        return None, "https://drive.google.com/drive/my-drive"

    DRIVE_FOLDER = "AgenteFO"
    MOUNT_PATH = "/content/drive"
    FOLDER_PATH = os.path.join(MOUNT_PATH, "My Drive", DRIVE_FOLDER)
    FALLBACK_URL = "https://drive.google.com/drive/my-drive"
    url_direta = FALLBACK_URL

    if not os.path.exists(os.path.join(MOUNT_PATH, "My Drive")):
        print("📂 Montando Google Drive...")
        try:
            drive.mount(MOUNT_PATH, force_remount=False)
            print("✅ Drive montado!")
        except Exception as e:
            print(f"⚠️  Aviso ao montar: {e}")
            os.makedirs("/tmp/agentefo_work", exist_ok=True)
            return "/tmp/agentefo_work", FALLBACK_URL
    else:
        print("✅ Google Drive já está montado!")

    print("\n🔐 Autenticando usuário para API do Drive...")
    try:
        auth.authenticate_user()
        print("✅ Autenticação concluída!")
    except Exception as e:
        print(f"⚠️  Aviso na autenticação: {e}")

    os.makedirs(FOLDER_PATH, exist_ok=True)
    os.chdir(FOLDER_PATH)

    try:
        service = build("drive", "v3")
        query = (
            f"name = '{DRIVE_FOLDER}' "
            "and mimeType = 'application/vnd.google-apps.folder' "
            "and trashed = false"
        )
        resultado = service.files().list(q=query, fields="files(id)").execute()
        arquivos = resultado.get("files", [])
        if arquivos:
            folder_id = arquivos[0]["id"]
            url_direta = f"https://drive.google.com/drive/folders/{folder_id}"
    except Exception:
        pass

    return FOLDER_PATH, url_direta


def show_loading_message():
    if ensure_in_colab():
        from IPython.display import display, HTML
        display(HTML("""
<style>
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
.loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
}
.spinner {
    width: 56px;
    height: 56px;
    border: 4px solid rgba(212, 175, 55, 0.15);
    border-top-color: #d4af37;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 24px;
}
.loading-text {
    color: #d4af37;
    font-family: monospace;
    font-size: 15px;
    animation: pulse 1.5s ease-in-out infinite;
}
</style>
<div class="loading-container">
    <div class="spinner"></div>
    <div class="loading-text">Carregando o AgenteFO...</div>
</div>
"""))
    else:
        print("⏳ Carregando o AgenteFO...")


def run():
    show_loading_message()

    print("\n" + "=" * 50)
    print("  🏢  INICIANDO AGENTEFO — FIO DE OURO")
    print("=" * 50)

    folder_path, drive_url = setup_auth_first()

    print(f"\n{next_joke()}")
    from setup_dependencies import run_all as setup_deps
    setup_deps()

    print(f"\n{next_joke()}")
    from setup_skills import install_skills
    install_skills()

    print(f"\n{next_joke()}")
    from launch_app import launch, set_drive_info
    set_drive_info(folder_path, drive_url)

    print(f"\n{next_joke()}")
    launch()

    print(f"\n ")


if __name__ == "__main__":
    run()
