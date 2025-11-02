# Guia de Debug para Automação na VPS

## Problemas Identificados e Soluções

### 1. Erro: "Chrome instance exited"
**Causa**: O código estava configurado para usar Microsoft Edge (Windows), mas a VPS usa Linux com Chromium.

**Solução Aplicada**:
- Modificado o código em `automacao_por_palavra.py` para detectar automaticamente o sistema operacional
- Adicionadas configurações headless necessárias para o Chromium
- Instaladas bibliotecas necessárias no Dockerfile

### 2. Erro: "Invalid requirement: 'a\x00t\x00t\x00r\x00s\x00=\x00=\x002\x005...'"
**Causa**: O arquivo `requirements.txt` estava em encoding UTF-16 (com caracteres nulos entre cada letra).

**Solução Aplicada**:
- Arquivo `requirements.txt` convertido para UTF-8 puro
- Criado script `validate_requirements.py` para validar o encoding
- Git configurado com `.gitattributes` para normalização automática

**Como Validar**:
```bash
python validate_requirements.py
```

**Como Corrigir Manualmente** (se necessário):
```bash
# No Windows (PowerShell):
Get-Content requirements.txt | Set-Content -Encoding utf8 requirements_new.txt
Move-Item -Force requirements_new.txt requirements.txt

# No Linux/Mac:
iconv -f UTF-16 -t UTF-8 requirements.txt > requirements_utf8.txt
mv requirements_utf8.txt requirements.txt
```

### 3. Configurações Headless Aplicadas

As seguintes opções foram adicionadas para garantir que o Chrome funcione sem interface gráfica:

```python
chrome_options.add_argument('--headless')              # Modo sem interface gráfica
chrome_options.add_argument('--no-sandbox')            # Necessário em ambientes Docker
chrome_options.add_argument('--disable-dev-shm-usage') # Evita problemas de memória compartilhada
chrome_options.add_argument('--disable-gpu')           # Desabilita GPU
chrome_options.add_argument('--window-size=1920,1080') # Define tamanho da janela virtual
```

## Como Testar Localmente

Para testar o código modificado no Windows (local):
```bash
python automacao_por_palavra.py
```

O código detectará automaticamente que está no Windows e usará Edge normalmente.

## Como Fazer Deploy na VPS

1. **Reconstruir a imagem Docker**:
```bash
docker-compose build
```

2. **Reiniciar o container**:
```bash
docker-compose down
docker-compose up -d
```

3. **Verificar os logs em tempo real**:
```bash
docker-compose logs -f scraper-comunica-email
```

## Como Depurar Erros na VPS

### Ver logs do container:
```bash
docker-compose logs scraper-comunica-email
```

### Ver logs detalhados do scheduler:
```bash
docker exec -it scraper-comunica-email cat /app/scheduler.log
```

### Entrar no container para debug:
```bash
docker exec -it scraper-comunica-email /bin/bash
```

### Dentro do container, testar o Chromium:
```bash
chromium --version
chromedriver --version
python -c "from selenium import webdriver; print('Selenium OK')"
```

### Testar manualmente o script dentro do container:
```bash
docker exec -it scraper-comunica-email python automacao_por_palavra.py
```

## Capturando Screenshots para Debug (NOVO - AUTOMÁTICO)

O código agora salva automaticamente screenshots em pontos críticos:

- `debug_01_pagina_inicial.png` - Página inicial do SIAFERIO
- `debug_02_usuario_preenchido.png` - Após preencher usuário
- `debug_03_antes_login.png` - Antes de clicar em login
- `debug_04_apos_login.png` - Após fazer login
- `debug_05_apos_ok_mensagem.png` - Após clicar OK na mensagem
- `debug_06_tela_comunicas.png` - Tela de comunicas
- `debug_erro_*.png` - Screenshots de erros (se houver)

### Baixar Screenshots Automaticamente

Use o script auxiliar (em ambiente com Docker CLI):

```bash
bash download_debug_screenshots.sh
```

Ou manualmente, um por um:

```bash
docker cp scraper-comunica-email:/app/debug_01_pagina_inicial.png ./
docker cp scraper-comunica-email:/app/debug_erro_usuario.png ./
# etc...
```

### Via EasyPanel

Se estiver usando EasyPanel, você pode acessar o terminal do container e usar:

```bash
# Listar screenshots disponíveis
ls -lh /app/debug_*.png

# Ver conteúdo base64 de um screenshot (para copiar)
base64 /app/debug_01_pagina_inicial.png
```

## Variáveis de Ambiente

Certifique-se de que o arquivo `.env` está presente na VPS com:
- USUARIO
- SENHA
- DESTINATARIOS
- EMAIL_REMETENTE
- SENHA_REMETENTE

**IMPORTANTE**: As variáveis NÃO devem ter espaços no início ou fim dos valores!

### ❌ Errado (com espaço):
```env
USUARIO=05512065785
SENHA= S441e
EMAIL_REMETENTE= user@gmail.com
```

### ✅ Correto (sem espaço):
```env
USUARIO=05512065785
SENHA=S441e
EMAIL_REMETENTE=user@gmail.com
```

**Nota**: O código agora usa `.strip()` automaticamente para remover espaços, mas é melhor manter o `.env` limpo.

## Ajustes de Timeouts

Se o site estiver lento na VPS, pode ser necessário aumentar os timeouts:

Em `automacao_por_palavra.py`:
- Linha 191: `wait = WebDriverWait(driver, 15)` - Aumentar para 30 se necessário
- Ajustar os `time.sleep()` conforme necessário

## Monitoramento de Recursos

Para verificar uso de CPU e memória do container:
```bash
docker stats scraper-comunica-email
```

## Logs de Erro Comuns

### "Message: session not created"
- Verifique se o chromium e chromedriver estão instalados
- Confirme que as opções headless estão sendo aplicadas

### "TimeoutException"
- Aumente os tempos de espera
- Verifique a conexão de rede da VPS

### "ElementNotInteractableException"
- O elemento pode não estar visível em modo headless
- Adicione `driver.save_screenshot()` para verificar

## Próximos Passos (Melhorias Futuras)

1. **Adicionar retry logic**: Se a automação falhar, tentar novamente automaticamente
2. **Logging melhorado**: Adicionar mais detalhes nos logs para facilitar debug
3. **Health checks**: Adicionar endpoint para verificar se o serviço está funcionando
4. **Alertas**: Notificar por email quando houver erros críticos
