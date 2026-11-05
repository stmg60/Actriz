# 🖥️ Fase 0: Entorno de Desarrollo (Arch Linux en VM)

Para evitar romper nuestro sistema principal, Actriz OS se desarrollará y probará dentro de una Máquina Virtual.

## Requisitos del Host
- VirtualBox, VMware o QEMU/KVM.
- 4 GB de RAM asignados a la VM (mínimo).
- 20 GB de disco duro virtual.

## Instalación de Arch Linux
1. Descargar la ISO oficial de Arch Linux: https://archlinux.org/download/
2. Arrancar la VM desde la ISO.
3. Seguir la guía oficial de instalación (o usar `archinstall` para una instalación rápida en texto).
4. **Importante:** Instalar el entorno gráfico X11 (no Wayland) y los drivers de video.
   `sudo pacman -S xorg-server xorg-xinit mesa`

## Usuario y Sudo
Crear un usuario llamado `actriz` y añadirlo al grupo `wheel` para tener privilegios de sudo.

## Habilitar Repositorio AUR
Instalar `yay` o `paru` para acceder a paquetes de la comunidad (como Picom, I3, etc.).
