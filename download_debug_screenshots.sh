#!/bin/bash
# Script para baixar screenshots de debug da VPS
# Uso: ./download_debug_screenshots.sh

echo "Baixando screenshots de debug do container..."

# Criar diretório local para screenshots
mkdir -p debug_screenshots

# Listar arquivos de debug disponíveis
echo ""
echo "Arquivos disponíveis no container:"
docker exec scraper-comunica-email ls -lh /app/debug_*.png 2>/dev/null || echo "Nenhum screenshot encontrado ainda"

echo ""
echo "Copiando screenshots..."

# Copiar todos os screenshots de debug
for file in debug_01_pagina_inicial.png \
            debug_02_usuario_preenchido.png \
            debug_03_antes_login.png \
            debug_04_apos_login.png \
            debug_05_apos_ok_mensagem.png \
            debug_06_tela_comunicas.png \
            debug_erro_usuario.png \
            debug_erro_senha.png \
            debug_erro_botao_ok.png \
            debug_erro_entrar_comunica.png \
            debug_aviso_sem_ok_mensagem.png; do

    docker cp scraper-comunica-email:/app/$file ./debug_screenshots/$file 2>/dev/null && \
        echo "  ✓ $file baixado" || \
        echo "  - $file não encontrado"
done

echo ""
echo "Screenshots salvos em: ./debug_screenshots/"
echo ""
echo "Para visualizar, abra os arquivos .png no diretório debug_screenshots/"
