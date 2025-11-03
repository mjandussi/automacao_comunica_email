"""
Scheduler para execução automática do scraper de Envio de Comunicas por Email
Roda (horário de Brasília) às 9, 11, 13, 15 e 17h
Pula sábados, domingos e feriados (nacionais + opcionais por estado/município)
"""

import os
import time
import logging
import sys
from datetime import datetime, date
from zoneinfo import ZoneInfo
import schedule

# --- Feriados ---
# pip install holidays
import holidays

# Importar a função main do scraper
from automacao_por_palavra import main

# ====================== Configurações ======================

# Timezone de referência para o agendador/log e para a regra de feriados
TZ_NAME = os.getenv("SCHEDULER_TZ", "America/Sao_Paulo")
TZ = ZoneInfo(TZ_NAME)

# Estado (UF) para feriados estaduais. Ex.: "RJ", "SP", etc. (opcional)
FERIADOS_UF = os.getenv("FERIADOS_UF", "").strip() or None

# Município (código IBGE) suportado pela lib em alguns países; no Brasil
# a cobertura municipal direta é limitada. Você pode manter None e usar
# sua lista customizada abaixo, se necessário.
FERIADOS_MUNICIPIO = None  # manter None por padrão

# Lista EXTRA de feriados próprios/locais (strings "YYYY-MM-DD" separadas por vírgula)
# Exemplo: "2025-01-20,2025-11-20"
FERIADOS_CUSTOM = {
    s.strip()
    for s in os.getenv("FERIADOS_CUSTOM", "").split(",")
    if s.strip()
}

# Horários (HH:MM) no TZ definido
HORARIOS = ["09:00", "11:00", "13:00", "15:00", "17:00"]

# Caminho opcional de log em arquivo
LOG_FILE_PATH = os.getenv("SCHEDULER_LOG_FILE", "").strip()

# ====================== Logging ======================

log_handlers = [logging.StreamHandler(sys.stdout)]
if LOG_FILE_PATH:
    log_handlers.append(logging.FileHandler(LOG_FILE_PATH, encoding="utf-8"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=log_handlers,
)
logger = logging.getLogger(__name__)

# ====================== Feriados BR ======================

def build_feriados_br(years: list[int]) -> holidays.HolidayBase:
    """
    Constrói o calendário de feriados para os anos informados, incluindo:
      - feriados nacionais do Brasil;
      - feriados estaduais (se FERIADOS_UF estiver definido);
      - (opcional) feriados municipais – cobertura limitada na lib;
      - feriados customizados via env FERIADOS_CUSTOM.
    """
    # A lib 'holidays' aceita BR() ou Brazil()
    cal = holidays.BR(prov=FERIADOS_UF, state=FERIADOS_UF, subdiv=FERIADOS_MUNICIPIO, years=years)
    # Adiciona feriados customizados
    for ds in FERIADOS_CUSTOM:
        try:
            y, m, d = map(int, ds.split("-"))
            cal[date(y, m, d)] = "Feriado (customizado)"
        except Exception:
            logger.warning(f"Data inválida em FERIADOS_CUSTOM: {ds!r} — ignorando.")
    return cal

# Pré-construímos para o ano corrente e vizinhos (para viradas de ano)
NOW_TZ = datetime.now(TZ)
FERIADOS = build_feriados_br([NOW_TZ.year - 1, NOW_TZ.year, NOW_TZ.year + 1])

# ====================== Funções ======================

def eh_fim_de_semana(d: date) -> bool:
    # Monday=0 ... Sunday=6
    return d.weekday() >= 5  # 5=sábado, 6=domingo

def eh_feriado(d: date) -> bool:
    # Verifica na base da lib + extras
    if d in FERIADOS:
        return True
    ds = d.strftime("%Y-%m-%d")
    return ds in FERIADOS_CUSTOM

def run_scraper():
    """Executa o scraper nos horários definidos, pulando fds e feriados (no TZ configurado)."""
    try:
        now = datetime.now(TZ)
        hoje = now.date()

        # Pula fim de semana
        if eh_fim_de_semana(hoje):
            logger.info(f"⏸️ Ignorado ({now.strftime('%A')}) — fim de semana no fuso {TZ_NAME}.")
            return

        # Pula feriado
        if eh_feriado(hoje):
            nome = FERIADOS.get(hoje) or "Feriado"
            logger.info(f"⏸️ Ignorado — {nome} ({hoje.isoformat()}) no fuso {TZ_NAME}.")
            return

        logger.info("=" * 60)
        logger.info(f"🚀 Scheduler disparado em {now.strftime('%d/%m/%Y às %H:%M:%S')} [{TZ_NAME}]")
        logger.info("=" * 60)

        main()

        logger.info("=" * 60)
        logger.info("✅ Scheduler concluído com sucesso!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"💥 ERRO no scheduler: {e}", exc_info=True)
        logger.error("=" * 60)

# ====================== Agendamentos ======================

# IMPORTANTE: 'schedule' usa o timezone do processo/SO.
# Como a checagem de fds/feriado e os logs usam TZ_NAME,
# é recomendável configurar o timezone do SO da VPS para America/Sao_Paulo
# (ou rodar o processo com TZ=America/Sao_Paulo no ambiente).

for hhmm in HORARIOS:
    schedule.every().day.at(hhmm).do(run_scraper)

# ====================== Inicialização ======================

logger.info("=" * 60)
logger.info("SCHEDULER INICIADO!")
logger.info(
    "Horários: %s (TZ: %s) — pula sábados, domingos e feriados%s%s.",
    ", ".join(HORARIOS),
    TZ_NAME,
    f" (UF={FERIADOS_UF})" if FERIADOS_UF else "",
    f" + {len(FERIADOS_CUSTOM)} custom" if FERIADOS_CUSTOM else "",
)
logger.info("Aguardando próxima execução...")
logger.info("=" * 60)

# ====================== Loop ======================

try:
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada 1 minuto
except KeyboardInterrupt:
    logger.info("Scheduler encerrado pelo usuário")
