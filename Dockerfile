# Use imagem Python slim
FROM python:3.11-slim

# Instalar dependências do sistema (Chrome headless)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libx11-6 \
    libxcomposite1 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Criar diretório para logs
RUN mkdir -p /var/log

# Comando padrão (executa scheduler que roda diariamente às 11:30)
CMD ["python", "scheduler.py"]
