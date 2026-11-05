#!/bin/bash
echo "🌸 Instalando Actriz OS..."
# Copiar configuraciones al molde
sudo cp -r ~/actriz/config/* /opt/actriz/entorno-grafico/ 2>/dev/null || sudo mkdir -p /opt/actriz/entorno-grafico/{i3,picom,kitty,rofi} && sudo cp -r ~/actriz/config/* /opt/actriz/entorno-grafico/
# Copiar binarios
sudo cp ~/actriz/bin/* /opt/actriz/bin/
sudo chmod +x /opt/actriz/bin/*.py /opt/actriz/bin/*.sh
# Configurar servicio Systemd
mkdir -p ~/.config/systemd/user/
cat << 'SYS' > ~/.config/systemd/user/actriz-islas.service
[Unit]
Description=Actriz OS Islands
After=graphical-session.target
[Service]
ExecStart=/bin/bash -c 'python3 /opt/actriz/bin/isla.py & python3 /opt/actriz/bin/isla_inferior.py & python3 /opt/actriz/bin/botes.py & wait'
Restart=always
[Install]
WantedBy=default.target
SYS
systemctl --user daemon-reload
systemctl --user enable --now actriz-islas.service
echo "✅ Actriz OS instalado."
