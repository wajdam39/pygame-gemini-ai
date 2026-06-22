# Używamy lekkiego obrazu Pythona z obsługą Debiana
FROM python:3.11-slim

# Instalacja zależności systemowych dla Pygame i serwera graficznego w kontenerze
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalacja bibliotek Pythona
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy kod gry
COPY . .

# NOWA, BEZPIECZNIEJSZA METODA TWORZENIA SKRYPTU STARTOWEGO
RUN printf '#!/bin/bash\n\
Xvfb :1 -screen 0 1280x720x24 &\n\
export DISPLAY=:1\n\
fluxbox &\n\
x11vnc -display :1 -nopw -listen localhost -xkb &\n\
/usr/share/novnc/utils/launch.sh --vnc localhost:5900 --listen ${PORT:-8080} &\n\
python gra_ai.py\n' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]