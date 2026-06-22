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

# SKRYPT STARTOWY: Python w tle, noVNC na pierwszym planie (obsługa portu Railway)
RUN printf '#!/bin/bash\n\
Xvfb :1 -screen 0 1280x720x24 &\n\
export DISPLAY=:1\n\
fluxbox &\n\
sleep 2\n\
x11vnc -display :1 -nopw -forever -listen localhost -xkb &\n\
sleep 2\n\
python gra_ai.py &\n\
sleep 2\n\
echo "Uruchamiam noVNC na porcie $PORT..."\n\
/usr/share/novnc/utils/launch.sh --vnc localhost:5900 --listen $PORT\n' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]