# Używamy oficjalnego obrazu Pythona
FROM python:3.11-slim

# Instalacja zależności systemowych dla Pygame, X11 oraz VNC
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    fluxbox \
    bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalacja bibliotek Pythona dla gry oraz serwera proxy dla noVNC
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt websockify

# Instalujemy noVNC bezpośrednio w kontenerze, żeby unikać problemów ze ścieżkami systemowymi
RUN apt-get update && apt-get install -y git && \
    git clone https://github.com/novnc/noVNC.git /app/novnc && \
    ln -s /app/novnc/vnc.html /app/novnc/index.html && \
    apt-get remove -y git && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Kopiujemy kod gry
COPY . .

# Tworzymy stabilny skrypt startowy z poprawnym przekazywaniem sygnałów
RUN printf '#!/bin/bash\n\
echo "Uruchamiam Xvfb..."\n\
Xvfb :1 -screen 0 1280x720x24 &\n\
export DISPLAY=:1\n\
\n\
echo "Uruchamiam Fluxbox..."\n\
fluxbox &\n\
sleep 2\n\
\n\
echo "Uruchamiam x11vnc..."\n\
x11vnc -display :1 -nopw -forever -listen localhost -xkb &\n\
sleep 2\n\
\n\
echo "Uruchamiam gre w tle..."\n\
python gra_ai.py &\n\
sleep 2\n\
\n\
echo "Uruchamiam serwer noVNC na porcie $PORT..."\n\
python -m websockify --web /app/novnc $PORT localhost:5900\n' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]