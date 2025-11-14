# --- Imports Selenium ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
# --- Imports de email ---
import smtplib
import email.message
# --- Outros Imports ---
import time
import re
import schedule
import html
import os
from pathlib import Path
from dotenv import load_dotenv
import traceback
import socket
import unicodedata



# Carrega as variáveis do arquivo .env
load_dotenv()

# ==============================================================================
# FUNÇÃO DE NORMALIZAÇÃO (REMOVE ACENTOS + MINÚSCULAS)
# ==============================================================================

def normalizar(txt: str) -> str:
    """
    Normaliza texto removendo acentos e convertendo para minúsculas.
    Isso torna as regex mais simples e robustas.
    """
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")  # remove acentos
    return txt.lower()

# --- Configurações pro Selenium e SIAFERIO ---
PATH_DO_DRIVER = "msedgedriver.exe"
url_do_siafe = "https://siafe2.fazenda.rj.gov.br/Siafe/faces/login.jsp"
USUARIO = os.getenv("USUARIO", "").strip()  # Remove espaços no início/fim
SENHA = os.getenv("SENHA", "").strip()  # Remove espaços no início/fim
DESTINATARIOS = os.getenv("DESTINATARIOS", "").strip()  # Remove espaços no início/fim

# Flag para controlar captura de screenshots de debug
DEBUG_SCREENSHOTS_ENABLED = os.getenv("DEBUG_SCREENSHOTS", "").strip().lower() in {"1", "true", "on", "yes"}
DEBUG_SCREENSHOT_DIR = os.getenv("DEBUG_SCREENSHOT_DIR", "/app").strip()


# ==============================================================================
# VARIÁVEIS
# ==============================================================================

setor_excluir_pesquisa = "SUGESC"
# Defina quantos comunicas você quer processar
#numero_de_comunicas_para_processar = 50 # Colocar um número alto para pegar todos

# ==============================================================================
# DICIONÁRIO DE ENVIO PRIORITÁRIO COM REGEX (TEXTO NORMALIZADO)
# ==============================================================================

DICIONARIO_DE_ENVIO_PRIORITARIO = {
    # ── SISTEMAS E TECNOLOGIA ──────────────────────────────────────────────────
    'Problemas SIAFERIO':
        r'\b(?:problema(?:s)?|erro(?:s)?|falha(?:s)?|indisponibilidade|instabilidade|lentidao)'
        r'(?:\s+(?:no|do|com|em))?\s+(?:siaferio|siafe[-\s]*rio|siaf[-\s]*e[-\s]*rio)\b'
        r'|\bsiaferio\s+(?:fora\s+do\s+ar|inoperante|com\s+problema(?:s)?|nao\s+(?:funciona|carrega|abre))\b',

    'FlexVision':
        r'\bflexvision\b|\bflex[-\s]*vision\b',

    'Sistemas Fora do Ar':
        r'\b(?:sistema(?:s)?|servico(?:s)?|aplicacao(?:oes)?)\s+(?:fora\s+do\s+ar|indisponivel(?:eis)?|inoperante(?:s)?)\b'
        r'|\b(?:sem\s+acesso|nao\s+(?:acessa|conecta|funciona))\s+(?:ao\s+)?(?:sistema(?:s)?|siaferio|siafem)\b'
        r'|\b(?:siaferio|siafe[-\s]*rio|siaf[-\s]*e[-\s]*rio|siafem|siaf[-\s]*em)\s+fora\s+do\s+ar\b',

    # ── URGÊNCIAS E PROBLEMAS CRÍTICOS ─────────────────────────────────────────
    'Urgente':
        r'\burgent(?:e|es?|issim[ao])\b|\bpriorit[aá]ri[ao](?:s)?\b|\bemerg[eê]ncia\b'
        r'|\basap\b|\bcom\s+urg[eê]ncia\b|\bpara\s+hoje\b|\bimediato\b',

    'Erro Crítico':
        r'\b(?:erro\s+(?:critico|grave|fatal|sistema)|falha\s+(?:critica|grave|geral))\b'
        r'|\b(?:nao\s+(?:consegue|consigo)|impossivel)\s+(?:acessar|executar|processar|finalizar)\b'
        r'|\bsistema\s+(?:travado|congelado|nao\s+responde)\b',


    # ── FECHAMENTO/FIM DE PERÍODO ──────────────────────────────────────────────
    'Fechamento':
        r'\b(?:fechamento|encerramento)\s+(?:do\s+)?(?:mes|periodo|exercicio|balanco)\b'
        r'|\bfim\s+do\s+(?:mes|ano|exercicio|periodo)\b'
        r'|\b(?:prestacao|envio)\s+de\s+contas?\b',

    'Relatório Urgente':
        r'\b(?:relatorio(?:s)?|demonstrativo(?:s)?)\s+(?:urgente(?:s)?|prioritario(?:s)?|para\s+(?:hoje|amanh[aã]))\b'
        r'|\b(?:balancete|dre|demonstracao)\s+(?:urgente|prioritari[ao])\b',
}

# --- Lista Simples de Palavras de ENVIO PRIORITÁRIO (mantida para compatibilidade) ---
PALAVRAS_DE_ENVIO_OBRIGATORIO = [
    'flexvision',  # mantida para compatibilidade com código existente
]


# ==============================================================================
# PADRÕES AUXILIARES PARA REUTILIZAÇÃO EM REGEX
# ==============================================================================

PREP = r'(?:de|do|da|dos|das|no|na|nos|nas)'
PT_OBJ = r'programa(?:s)?\s*(?:de|-)?\s*trabalho(?:s)?'   # "programa(s) de trabalho(s)"
ACOES = r'(?:cadastr(?:o(?:s)?|ar|ado(?:s)?|amento|ou)|libera(?:cao|r|do(?:s)?)|inativa(?:cao|r|do(?:s)?))'

# ==============================================================================
# DICIONÁRIO DE BLOQUEIO COM REGEX ROBUSTAS (TEXTO NORMALIZADO)
# ==============================================================================

DICIONARIO_DE_BLOQUEIO_REGEX = {
    # ── PARTE CADASTRAL FINANCEIRA ───────────────────────────────────────────────
    'Inscricao Generica':
        r'\binscri(?:cao|coes)\s+generica(?:s)?\b|\bigs\b',

    'Credor Generico':
        r'\bcredor(?:es)?\s+generic(?:o|os)\b|\bcgs\b',

    'Bloqueio Judicial':
        r'\bbloqueio(?:s)?\s+judicia(?:l|is)\b|\bcriaca(?:o|oes)\s+de\s+bj\b|\bbj\b',

    'Codigo de Barras':
        r'\b(?:cod(?:\.|\s*)barras?|codigo(?:s)?\s+de\s+barras?)\b'
        r'|\balterac(?:ao|oes)\s+de\s+cnpj\s+em\s+(?:cod(?:\.|\s*)barras?|codigo\s+de\s+barras?)\b',

    'Dados Bancarios':
        r'\bdados\s+bancari(?:o|os)\b'
        r'|\bdomicilio\s+bancari(?:o|os)\b'
        r'|\b(alterac(?:ao|oes)|cadastro|atualizac(?:ao|oes))\s+(?:de\s+)?'
        r'(?:banco(?:s)?|agencia(?:s)?|conta(?:s)?\s+corrent(?:e|es))\b',

    'Boleto/Credor':
        r'\bboletos?\b|\bcredor(?:es)?\b',

    # ── PARTE CADASTRAL ─────────────────────────────────────────────────────────
    'Cadastro em Geral':
        r'\binformac(?:oes)?\s+cadastrais\b'
        r'|\brequisic(?:ao|oes)\s+de\s+pequeno(?:s)?\s+valor(?:es)?\b',

    'Cadastro de Convenio':
        r'\bcadastro(?:s)?\s+(?:de\s+)?conta(?:s)?\s+(?:de\s+)?convenio(?:s)?\b'
        r'|\bconta(?:s)?\s+(?:de\s+)?convenio(?:s)?\s+cadastrad(?:a|as|o|os)\b',

    'Atualizacao de Dados':
        r'\batualizac(?:ao|oes)\s+(?:de\s+)?dados?\b'
        r'|\bnomeac(?:ao|oes)\s+de\s+contador(?:es)?\b'
        r'|\balterar?\s+nome(?:s)?\s+(?:de|das|nas)\s+unidade(?:s)?\s+gestora(?:s)?\b',

    # **Programa de Trabalho** (ordem ação→objeto OU objeto→ação)
    'Programa de Trabalho':
        r'\b(?:'
        rf'(?:{ACOES}(?:\s+(?:o|a|os|as))?\s*(?:\s+no\s+sistema)?(?:\s+{PREP})?\s+{PT_OBJ})'
        r'|'
        rf'(?:{PT_OBJ}(?:\s+no\s+sistema)?(?:\s+(?:foi|foram|esta(?:o)?|sera(?:o)?))?\s*(?:\w+\s+){{0,6}}{ACOES})'
        r')\b',

    'Detalhamento de Fonte':
        r'\bcadastro(?:s)?\s+(?:de\s+)?detalhamento(?:s)?\s+(?:de\s+)?fonte(?:s)?\b'
        r'|\bdetalhamento(?:s)?\s+(?:da|de)\s+fonte(?:s)?\b'
        r'|\bfonte(?:s)?\s+detalhad(?:a|as|o|os)\b',

    # ── ACESSO E PERFIL ─────────────────────────────────────────────────────────
    'Acesso ou Senha':
        r'(?:(?:\bacesso(?:s)?\b|\bsenha(?:s)?\b).{0,25}\b(?:siafem|siaferio)\b|\bsiafem\b|\bsiaferio\b)',

    'Reativacao':
        r'\breativ(?:ar|acao|acoes|ado(?:s)?|ada(?:s)?)\b'
        r'|\bdesbloqueio(?:s)?\s+de\s+usuario(?:s)?\b'
        r'|\breativac(?:ao|oes)\s+de\s+perfil\b',

    'Perfil ou Gestor de Usuarios':
        r'\bgestor(?:es)?\s+de\s+usuario(?:s)?\b'
        r'|\bperfil(?:es)?\s+de\s+usuario(?:s)?\b'
        r'|\btroca\s+de\s+gestor\b',

    # ── OUTROS ──────────────────────────────────────────────────────────────────
    'LISCONTIR':
        r'\bliscontir\b|\bdesbloqueio\s+de\s+empenho(?:s)?\b',

    'Desconsiderar':
        r'\bdesconsiderar\b',
}



# Configurações de e-mail
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "").strip()
SENHA_REMETENTE = os.getenv("SENHA_REMETENTE", "").strip()


def salvar_screenshot_debug(driver, nome_arquivo, descricao=""):
    """Salva screenshots de debug apenas quando habilitado por variável de ambiente."""
    if not DEBUG_SCREENSHOTS_ENABLED:
        return

    destino = Path(nome_arquivo)
    if DEBUG_SCREENSHOT_DIR:
        destino = Path(DEBUG_SCREENSHOT_DIR) / nome_arquivo

    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        driver.save_screenshot(str(destino))
        if descricao:
            print(f"[DEBUG] Screenshot salvo ({descricao}): {destino}")
        else:
            print(f"[DEBUG] Screenshot salvo: {destino}")
    except Exception as err:
        print(f"[DEBUG] Falha ao salvar screenshot '{nome_arquivo}': {err}")

        

def enviar_email(destinatarios, assunto, corpo_html):
    try:
        msg = email.message.Message()
        msg['Subject'] = assunto
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = destinatarios
        msg.add_header('Content-Type', 'text/html')
        msg.set_payload(corpo_html, 'iso-8859-1')

        s = smtplib.SMTP('smtp.gmail.com: 587')
        s.starttls()
        s.login(EMAIL_REMETENTE, SENHA_REMETENTE)
        s.sendmail(EMAIL_REMETENTE, destinatarios.split(';'), msg.as_string().encode('iso-8859-1'))
        s.quit()
        print("--> E-mail enviado com sucesso.")
        return True
    except Exception as e:
        print(f"--> ERRO AO ENVIAR E-MAIL: {e}")
        return False




def enviar_alerta_falha(exc: Exception, log_da_execucao, driver=None):
    """Manda e-mail SOMENTE quando ocorre erro na automação."""
    tb = traceback.format_exc()
    host = socket.gethostname()
    url_atual = ""
    try:
        if driver:
            url_atual = getattr(driver, "current_url", "")
    except:
        pass

    # Reaproveita seu formatador de log
    try:
        log_html = formatar_log_para_html(log_da_execucao)
    except Exception:
        log_html = "<i>(Falha ao formatar log)</i>"

    corpo_html = f"""
    <div style="font-family:Arial, sans-serif; line-height:1.5">
      <h3>🛑 Falha na Automação</h3>
      <p><b>Host:</b> {host}</p>
      <p><b>URL atual:</b> {html.escape(url_atual)}</p>
      <p><b>Erro:</b> <code>{html.escape(repr(exc))}</code></p>
      <p><b>Traceback:</b></p>
      <pre style="white-space:pre-wrap">{html.escape(tb)}</pre>
      <hr>
      <h4>Log parcial da execução</h4>
      <div style="border:1px solid #ddd; padding:10px; background:#f9f9f9">{log_html}</div>
    </div>
    """
    enviar_email(
        destinatarios=DESTINATARIOS,
        assunto=f"🛑 Falha na Automação (host {host})",
        corpo_html=corpo_html
    )



# ==============================================================================
# FUNÇÕES AUXILIARES 
# ==============================================================================
    

def formatar_log_para_html(lista_de_logs):
    """
    Processa a lista de logs e a transforma em um HTML bem formatado,
    com separadores, cores e destaques.
    """
    html_lines = []
    # Itera sobre cada linha de log que foi registrada
    for linha in lista_de_logs:
        # Pula linhas em branco para não poluir o log
        if not linha.strip():
            continue

        linha_segura = html.escape(linha).strip()

        # --- AQUI COMEÇA A NOVA LÓGICA DE FORMATAÇÃO ---

        # 1. Destaca a linha do ID do Comunica
        # Usamos regex para encontrar a linha do ID e formatar apenas o número
        padrao_id = r"(--- ID do comunica )(\d+)( ---)"
        match = re.search(padrao_id, linha_segura)
        if match:
            # Remonta a linha, colocando o ID em negrito e com fundo amarelo claro
            linha_formatada = f'{match.group(1)}<b style="background-color: #fcf8e3; padding: 2px 5px; border-radius: 3px;">{match.group(2)}</b>{match.group(3)}'
        
        # 2. Transforma as linhas de verificação em títulos e adiciona um separador
        elif "--- Verificando a lista de comunicas..." in linha_segura:
            # Adiciona uma linha horizontal ANTES de cada novo bloco de verificação (exceto o primeiro)
            if html_lines:
                html_lines.append('<hr style="border: none; border-top: 1px dashed #ccc; margin: 20px 0;">')
            linha_formatada = f'<h4>{linha_segura}</h4>'

        # 3. Colore as linhas de status (como antes)
        elif "[BLOQUEADO]" in linha_segura:
            linha_formatada = f'<div style="color: #d9534f; font-weight: bold;">{linha_segura}</div>' # Vermelho
        elif "[ENVIO DE EMAIL PARA ANALISE]" in linha_segura:
            linha_formatada = f'<div style="color: #5cb85c; font-weight: bold;">{linha_segura}</div>' # Verde
        elif "[INFORMATIVO]" in linha_segura:
             linha_formatada = f'<div style="color: #5bc0de; font-weight: bold;">{linha_segura}</div>' # Azul
        elif "[ENVIO PRIORITÁRIO]" in linha_segura:
             linha_formatada = f'<div style="color: #bc0ec7; font-weight: bold;">{linha_segura}</div>' # Roxo
        

        # 4. Linhas normais (sem formatação especial)
        else:
            linha_formatada = linha_segura
        
        html_lines.append(linha_formatada)
    
    # Junta todas as linhas HTML formatadas com uma quebra de linha
    return "<br>".join(html_lines)

# ==============================================================================
# AUTOMAÇÃO (FLUXO PRINCIPAL)
# ==============================================================================

def main():

    """
    Esta função contém todo o ciclo de automação, desde o login até o fim.
    Será chamada pelo agendador nos horários programados.
    """
    # A LISTA DE LOG É CRIADA NO INÍCIO DE CADA EXECUÇÃO
    log_da_execucao = []
    
    # A FUNÇÃO DE LOG É INTERNA E USA A LISTA LOCAL
    def registrar_log(mensagem):
        """Função interna que usa a lista 'log_desta_execucao'."""
        print(mensagem)
        log_da_execucao.append(mensagem)


    #registrar_log(f"Automação realizada para {numero_de_comunicas_para_processar} comunica(s).")
    time.sleep(2)

    # --- INÍCIO DA AUTOMAÇÃO COM SELENIUM (VERSÃO CORRIGIDA) ---
    print("Iniciando navegador com Selenium...")

    # Detectar se está rodando em ambiente Docker/Linux (VPS) ou Windows (local)
    import platform
    sistema = platform.system()

    if sistema == "Linux":
        # Configuração para ambiente headless (VPS/Docker)
        print("Ambiente Linux detectado. Usando Chromium headless...")
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Usar chromium instalado no sistema
        chrome_options.binary_location = '/usr/bin/chromium'
        service = Service('/usr/bin/chromedriver')

        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        # Configuração para ambiente Windows (local)
        print("Ambiente Windows detectado. Usando Edge...")
        driver = webdriver.Edge()

    driver.get(url_do_siafe)
    print("Página de login aberta")

    # Salva screenshot inicial apenas quando debug está habilitado
    salvar_screenshot_debug(driver, "debug_01_pagina_inicial.png", "página inicial")

    try:
        # Cria um objeto de espera. Aumentei para 30s para dar mais margem em ambientes lentos.
        wait = WebDriverWait(driver, 30)

        print("Aguardando campo de usuário...")
        # AÇÕES NA TELA DE LOGIN
        try:
            campo_usuario = wait.until(EC.element_to_be_clickable((By.ID, "loginBox:itxUsuario::content")))
            print(f"Campo de usuário encontrado. Preenchendo com usuário...")
            campo_usuario.clear()
            campo_usuario.send_keys(USUARIO)
            time.sleep(2)

            # Screenshot após preencher usuário (opcional)
            salvar_screenshot_debug(driver, "debug_02_usuario_preenchido.png", "usuário preenchido")

        except Exception as e:
            print(f"ERRO ao localizar/preencher campo de usuário: {e}")
            salvar_screenshot_debug(driver, "debug_erro_usuario.png", "erro ao preencher usuário")
            if DEBUG_SCREENSHOTS_ENABLED:
                try:
                    print(f"HTML da página: {driver.page_source[:500]}")  # Primeiros 500 caracteres
                except Exception as html_err:
                    print(f"Falha ao obter HTML para debug: {html_err}")
            raise

        print("Aguardando campo de senha...")
        try:
            campo_senha = wait.until(EC.element_to_be_clickable((By.ID, "loginBox:itxSenhaAtual::content")))
            print(f"Campo de senha encontrado. Preenchendo...")
            campo_senha.clear()
            campo_senha.send_keys(SENHA)
            time.sleep(2)
        except Exception as e:
            print(f"ERRO ao localizar/preencher campo de senha: {e}")
            salvar_screenshot_debug(driver, "debug_erro_senha.png", "erro ao preencher senha")
            raise

        print("Aguardando botão OK...")
        try:
            botao_ok = wait.until(EC.element_to_be_clickable((By.ID, "loginBox:btnConfirmar")))
            print("Botão OK encontrado. Clicando...")
            # Screenshot antes de clicar
            salvar_screenshot_debug(driver, "debug_03_antes_login.png", "antes de clicar em login")
            botao_ok.click()
            print("Botão OK clicado. Aguardando resposta...")
        except Exception as e:
            print(f"ERRO ao localizar/clicar botão OK: {e}")
            salvar_screenshot_debug(driver, "debug_erro_botao_ok.png", "erro ao clicar em OK")
            raise

        # Aguardar o redirecionamento após o login (espera a URL mudar)
        print("Aguardando redirecionamento pós-login...")
        time.sleep(5)

        # Screenshot após login
        salvar_screenshot_debug(driver, "debug_04_apos_login.png", "após login")
        if DEBUG_SCREENSHOTS_ENABLED:
            print(f"URL atual: {driver.current_url}")

        # AÇÕES NA TELA DE MENSAGEM PÓS-LOGIN

        print("Procurando botão OK da mensagem pós-login...")

        # Estratégia 1: Tentar pelo ID original
        botao_ok_encontrado = False
        try:
            print("Tentativa 1: Procurando por ID completo...")
            botao_ok_mensagem_tela = wait.until(EC.element_to_be_clickable((By.ID, "pt1:warnMessageDec:frmExec:btnNewWarnMessageOK")))
            print("✓ Botão OK mensagem encontrado pelo ID. Clicando...")
            botao_ok_mensagem_tela.click()
            botao_ok_encontrado = True
            time.sleep(4)

            salvar_screenshot_debug(driver, "debug_05_apos_ok_mensagem.png", "após confirmar mensagem")

        except Exception as e1:
            print(f"Tentativa 1 falhou: {e1}")

            # Estratégia 2: Tentar por CSS Selector parcial
            try:
                print("Tentativa 2: Procurando por CSS Selector parcial...")
                botao_ok_mensagem_tela = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[id*='btnNewWarnMessageOK']")))
                print("✓ Botão OK mensagem encontrado por CSS. Clicando...")
                botao_ok_mensagem_tela.click()
                botao_ok_encontrado = True
                time.sleep(4)

                salvar_screenshot_debug(driver, "debug_05_apos_ok_mensagem.png", "após confirmar mensagem")

            except Exception as e2:
                print(f"Tentativa 2 falhou: {e2}")

                # Estratégia 3: Tentar por texto do botão (se for OK)
                try:
                    print("Tentativa 3: Procurando botão com texto 'OK'...")
                    botao_ok_mensagem_tela = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'OK') or @value='OK']")))
                    print("✓ Botão OK mensagem encontrado por texto. Clicando...")
                    botao_ok_mensagem_tela.click()
                    botao_ok_encontrado = True
                    time.sleep(4)

                    salvar_screenshot_debug(driver, "debug_05_apos_ok_mensagem.png", "após confirmar mensagem")

                except Exception as e3:
                    print(f"Tentativa 3 falhou: {e3}")
                    print("AVISO: Botão OK mensagem não encontrado por nenhuma estratégia (pode não existir)")
                    # Salva screenshot para análise
                    salvar_screenshot_debug(driver, "debug_aviso_sem_ok_mensagem.png", "sem botão OK pós-login")
                    if DEBUG_SCREENSHOTS_ENABLED:
                        print(f"URL atual: {driver.current_url}")
                        print("Continuando sem clicar no botão OK...")

        print("Aguardando botão de entrar em comunica...")
        try:
            botao_entrar_comunica = wait.until(EC.element_to_be_clickable((By.ID, "pt1:itLinks:1:j_id__ctru33")))
            print("Botão entrar comunica encontrado. Clicando...")
            botao_entrar_comunica.click()

            # Pausa final para garantir que a página principal carregou completamente
            # antes de o robô prosseguir para a próxima parte da automação (tela de comunicas).
            time.sleep(10)

            salvar_screenshot_debug(driver, "debug_06_tela_comunicas.png", "tela de comunicas")
            if DEBUG_SCREENSHOTS_ENABLED:
                print(f"URL atual: {driver.current_url}")

        except Exception as e:
            print(f"ERRO ao localizar/clicar botão entrar comunica: {e}")
            salvar_screenshot_debug(driver, "debug_erro_entrar_comunica.png", "erro ao entrar em comunicas")
            if DEBUG_SCREENSHOTS_ENABLED:
                print(f"URL atual: {driver.current_url}")
            raise 

        # AÇÕES NA TELA DE COMUNICAS (FILTRO)
        
        botao_de_filtro = wait.until(EC.element_to_be_clickable((By.ID, "pt1:binbox:messagesTableViewer:sdtFilter::disAcr")))
        botao_de_filtro.click()
        time.sleep(1)
        botao_de_propriedade = wait.until(EC.element_to_be_clickable((By.ID, "pt1:binbox:messagesTableViewer:table_rtfFilter:0:cbx_col_sel_rtfFilter::content")))
        botao_de_propriedade.click()
        time.sleep(4) 
        # ESCOLHA DO ORIGEM REMETENTE >> Enviamos a letra "R" e a tecla "Enter" para o mesmo elemento que acabamos de clicar
        botao_de_propriedade.send_keys("O" + Keys.ENTER)
        time.sleep(4) 
        botao_de_negar = wait.until(EC.element_to_be_clickable((By.ID, "pt1:binbox:messagesTableViewer:table_rtfFilter:0:chk_neg_rtfFilter::content")))
        botao_de_negar.click()
        time.sleep(2) 
        botao_de_operador = wait.until(EC.element_to_be_clickable((By.ID, "pt1:binbox:messagesTableViewer:table_rtfFilter:0:cbx_op_sel_rtfFilter::content")))
        botao_de_operador.click()
        time.sleep(4) 
        # ESCOLHA DO TERMINA COM >> Enviamos a letra "T" e a tecla "Enter" para o mesmo elemento que acabamos de clicar
        botao_de_operador.send_keys("T" + Keys.ENTER)
        time.sleep(4)
        campo_valor_filtro = wait.until(EC.element_to_be_clickable((By.ID, "pt1:binbox:messagesTableViewer:table_rtfFilter:0:in_value_rtfFilter::content")))
        campo_valor_filtro.send_keys(setor_excluir_pesquisa)
        time.sleep(4) 
        campo_valor_filtro.send_keys(Keys.TAB)
        time.sleep(20) 

        # --- LOOP DINÂMICO PARA PROCESSAR TODOS OS ITENS ATÉ A LISTA FICAR VAZIA ---

        # Inicializamos um contador para o log
        comunicas_processados_neste_ciclo = 0

        while True:
            registrar_log(f"\n--- Verificando a lista de comunicas... ---")
            
            # VERIFICAÇÃO: AINDA EXISTEM COMUNICAS NA LISTA?
            
            # >>> A MUDANÇA ESTÁ AQUI <<<
            # Este seletor CSS é muito mais preciso. Ele procura por QUALQUER elemento que:
            # 1. Comece com (id^=) 'pt1:binbox:messagesTableViewer:tabViewerDec:'
            # 2. E termine com (id$=) ':j_id8'
            seletor_preciso_comunica = "[id^='pt1:binbox:messagesTableViewer:tabViewerDec:'][id$=':j_id8']"
            lista_de_comunicas = driver.find_elements(By.CSS_SELECTOR, seletor_preciso_comunica)
            
            # Se a lista que o Selenium encontrou estiver vazia, significa que não há mais itens.
            if not lista_de_comunicas: # 'if not lista' é uma forma mais Pythonica de checar se a lista está vazia
                registrar_log("[INFORMATIVO] Fim da lista detectado. Não há mais comunicas para processar.")
                break # Interrompe o loop while True
                
            registrar_log(f"Encontrados {len(lista_de_comunicas)} comunica(s) na lista. Processando o primeiro...")
            comunicas_processados_neste_ciclo += 1
            
            # AÇÃO: PROCESSAR O PRIMEIRO ITEM DA LISTA
            
            # Clicamos no primeiro elemento da lista que acabamos de encontrar
            primeiro_comunica_da_lista = lista_de_comunicas[0]
            primeiro_comunica_da_lista.click()
            time.sleep(4)
            
            # O botão de visualizar continua o mesmo
            botao_de_visualizar = wait.until(EC.element_to_be_clickable((By.ID, "pt1:binbox:messagesTableViewer:btnView")))
            botao_de_visualizar.click()
            time.sleep(30)
            
            # EXTRAÇÃO DE DADOS (Lógica permanece a mesma)

            # COPIAR O NUMERO DO COMUNICA
            elemento_id = wait.until(EC.visibility_of_element_located((By.ID, "pt1:m1:itxIdentificador::content")))
            numero_comunica_copiado = elemento_id.text.strip()

            # COPIAR O ASSUNTO DO COMUNICA
            assunto_comunica = wait.until(EC.visibility_of_element_located((By.ID, "pt1:m1:txtSubject::content")))
            assunto_comunica_copiado = assunto_comunica.text.strip()
            
            # COPIAR O TEXTO DO COMUNICA (IFRAME)
            wait.until(EC.frame_to_be_available_and_switch_to_it(2))
            corpo_do_iframe = wait.until(EC.visibility_of_element_located((By.TAG_NAME, "body")))
            comunica_recebido = corpo_do_iframe.text.strip()
            driver.switch_to.default_content()

            # NORMALIZAÇÃO DO TEXTO (remove acentos + minúsculas)
            comunica_normalizado = normalizar(comunica_recebido)

            # Botão de "Sair" da visualização do Comunica
            botao_de_sair_comunica = wait.until(EC.element_to_be_clickable((By.ID, "pt1:m1:btnVoltar")))
            botao_de_sair_comunica.click()
            time.sleep(20) # Tempo para a lista principal recarregar
            
            registrar_log(f"--- Análise do Comunica ID '{numero_comunica_copiado} - {assunto_comunica_copiado}' ---")


            
            # #######################################################################
            # INÍCIO DA NOVA LÓGICA DE DECISÃO HIERÁRQUICA
            # #######################################################################

            email_deve_ser_enviado = False
            motivo_da_decisao = ""

            # ETAPA A: Verificação de Prioridade (Envio Obrigatório)
            # Usa texto normalizado para busca mais robusta
            encontrou_prioritaria = False
            conceito_prioritario = ""
            trecho_prioritario = ""
            
            # A1: Verificar dicionário de prioridades com REGEX
            for conceito, padrao in DICIONARIO_DE_ENVIO_PRIORITARIO.items():
                match = re.search(padrao, comunica_normalizado, flags=re.IGNORECASE|re.DOTALL)
                if match:
                    encontrou_prioritaria = True
                    conceito_prioritario = conceito
                    trecho_prioritario = match.group(0)
                    motivo_da_decisao = f"[ENVIO PRIORITÁRIO] {conceito_prioritario} detectado (trecho: \"{trecho_prioritario}\")."
                    break
            
            # A2: Se não encontrou no dicionário, verifica a lista simples (compatibilidade)
            if not encontrou_prioritaria:
                for palavra in PALAVRAS_DE_ENVIO_OBRIGATORIO:
                    palavra_normalizada = normalizar(palavra)
                    padrao = r'\b' + re.escape(palavra_normalizada) + r'\b'
                    if re.search(padrao, comunica_normalizado, re.IGNORECASE):
                        encontrou_prioritaria = True
                        motivo_da_decisao = f"[ENVIO PRIORITÁRIO] Palavra-chave '{palavra}' encontrada."
                        break

            if encontrou_prioritaria:
                email_deve_ser_enviado = True

            else:
                # ETAPA B: Verificação de Bloqueio com REGEX melhoradas (Só se não for prioritário)
                # Texto normalizado para as buscas de bloqueio
                texto = comunica_normalizado
                
                encontrou_bloqueio = False
                conceito_encontrado = ""
                trecho_casado = ""

                # Itera sobre o dicionário de padrões de regex
                for conceito, padrao in DICIONARIO_DE_BLOQUEIO_REGEX.items():
                    match = re.search(padrao, texto, flags=re.IGNORECASE|re.DOTALL)
                    if match:
                        encontrou_bloqueio = True
                        conceito_encontrado = conceito
                        trecho_casado = match.group(0)
                        break

                if encontrou_bloqueio:
                    email_deve_ser_enviado = False
                    motivo_da_decisao = f"[BLOQUEADO] Assunto impeditivo: '{conceito_encontrado}' (trecho: \"{trecho_casado}\")."


                else:
                    # ETAPA C: Caso Padrão (Nenhuma palavra especial encontrada)
                    email_deve_ser_enviado = True
                    motivo_da_decisao = "[ENVIO DE EMAIL PARA ANALISE] Nenhuma palavra impeditiva encontrada."

            # BLOCO DE AÇÃO FINAL (Toma a ação baseada na decisão)
            registrar_log(motivo_da_decisao)

            if email_deve_ser_enviado:
                registrar_log("################# E-mail do Comunica enviado ######################")
                comunica_formatado = comunica_recebido.replace('\n', '<br>')
                corpo_email_comunica = f"""
                <p>Prezados,</p>
                <p>Segue abaixo o comunica ({numero_comunica_copiado} - {assunto_comunica_copiado}) extraído da automação:</p>
                <div style="border: 1px solid #ccc; padding: 10px; font-family: monospace; background-color: #f9f9f9;">
                    {comunica_formatado}
                </div>
                <p>---</p>
                <p>Este é um e-mail automático.</p>
                """
                enviar_email(
                    destinatarios=DESTINATARIOS,
                    assunto=f'Comunica ({numero_comunica_copiado} - {assunto_comunica_copiado}) Processado Automaticamente - {time.strftime("%d/%m/%Y")}',
                    corpo_html=corpo_email_comunica
                )
            else:
                registrar_log("################# E-mail Não enviado ######################")
                continue



#############################################################################################################################################################

    # Bloco de exceção e finalização permanecem os mesmos
    except Exception as e:
        print(f"Ocorreu um erro durante a automação: {e}")
        # dispara e-mail SOMENTE em caso de erro
        try:
            enviar_alerta_falha(e, log_da_execucao, driver)
        finally:
            # opcional: re-lançar para manter código de saída e logs de erro
            raise



    finally:
        registrar_log("\n--- Finalizando ciclo ---")
        if driver:
            try:
                driver.quit()
                registrar_log("Navegador fechado.")
            except Exception as e:
                registrar_log(f"Erro ao fechar navegador: {e}")
        
        # ==============================================================================
        # ENVIO DO LOG FINAL (APÓS O FIM DO LOOP)
        # ==============================================================================

        registrar_log("\n--- Fim do processamento de todos os comunicas ---")

        # --- AQUI ESTÁ A MUDANÇA: Usamos a nova função para formatar o log ---
        log_final_formatado_html = formatar_log_para_html(log_da_execucao)

        # --- O corpo do e-mail agora usa um estilo mais limpo ---
        corpo_email_log = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h3>Log de Processamento do Robô</h3>
            <p>Análise só com Palavras Chave</p>
            <p>Execução finalizada em: {time.strftime("%d/%m/%Y às %H:%M:%S")}</p>
            <hr>
            <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9;">
                {log_final_formatado_html}
            </div>
            <hr>
            <p>Este é um e-mail de resumo automático.</p>
        </div>
        """

        enviar_email(
            destinatarios=DESTINATARIOS, 
            assunto=f'Log da Automação de Comunicas às {time.strftime("%d/%m/%Y %H:%M:%S")}', 
            corpo_html=corpo_email_log
        )



#############################################################################################################################################################


# ==============================================================================
# . AGENDAMENTO E EXECUÇÃO (O "GUARDIÃO")
# ==============================================================================
print("----------------------------------")
print("--- Robô de Comunicas Iniciado ---")
print("Análise só com Palavras Chave e uso de Regex")
print("----------------------------------")





# EXECUTAR
# python final_palavra.py


if __name__ == "__main__":
    main()
