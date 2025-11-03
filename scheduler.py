"""
Scheduler para execução automática do scraper de Envio de Comunicas por Email
Roda diariamente às 9, 12, 15 e 18h (horário de Brasília)
"""

import os
import time
import logging
import sys
from datetime import datetime
import schedule

# Importar a função main do scraper
from automacao_por_palavra import main

# Configurar logging
log_handlers = [logging.StreamHandler(sys.stdout)]

log_file_path = os.getenv("SCHEDULER_LOG_FILE", "").strip()
if log_file_path:
    # Permite habilitar log em arquivo apenas quando configurado explicitamente
    log_handlers.append(logging.FileHandler(log_file_path, encoding='utf-8'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=log_handlers,
)
logger = logging.getLogger(__name__)


def run_scraper():
    """Executa o scraper e trata erros"""
    try:
        now = datetime.now()
        logger.info("=" * 60)
        logger.info(f"Scheduler disparado em {now.strftime('%d/%m/%Y às %H:%M:%S')}")
        logger.info("=" * 60)

        # Executar o scraper
        main()

        logger.info("=" * 60)
        logger.info("Scheduler concluído com sucesso!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"ERRO no scheduler: {e}", exc_info=True)
        logger.error("=" * 60)


#### Agendando a função para os horários desejados
schedule.every().day.at("09:00").do(run_scraper)
schedule.every().day.at("11:00").do(run_scraper)
schedule.every().day.at("13:00").do(run_scraper)
schedule.every().day.at("15:00").do(run_scraper)
schedule.every().day.at("17:00").do(run_scraper)

# Mensagem de inicialização
logger.info("=" * 60)
logger.info("SCHEDULER INICIADO!")
logger.info("Horário configurado: diariamente as 9, 12, 15 e 18 horas")
logger.info("Timezone: America/Sao_Paulo")
logger.info("Aguardando próxima execução...")
logger.info("=" * 60)

# Loop infinito mantém o script rodando
try:
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada 1 minuto
except KeyboardInterrupt:
    logger.info("Scheduler encerrado pelo usuário")


# python scheduler.py
