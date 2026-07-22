#!/usr/bin/env bash
# One-time bootstrap on Ubuntu 22.04/24.04 (Hetzner CPX11 or similar).
# Run as root or with sudo:  bash hetzner-setup.sh
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Nyong-1104/nyong-1104.github.io.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/pokepop}"
CRON_USER="${CRON_USER:-pokepop}"
PYTHON="${PYTHON:-python3}"

echo "==> System packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git ca-certificates curl tzdata "${PYTHON}" "${PYTHON}-venv"

echo "==> Timezone Asia/Seoul (cron at KST midnight)"
timedatectl set-timezone Asia/Seoul || ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime

echo "==> User: ${CRON_USER}"
if ! id "${CRON_USER}" &>/dev/null; then
  useradd -m -s /bin/bash "${CRON_USER}"
fi

echo "==> Clone repo -> ${INSTALL_DIR}"
mkdir -p "$(dirname "${INSTALL_DIR}")"
if [[ ! -d "${INSTALL_DIR}/.git" ]]; then
  git clone "${REPO_URL}" "${INSTALL_DIR}"
fi
chown -R "${CRON_USER}:${CRON_USER}" "${INSTALL_DIR}"

echo "==> Python venv + Playwright"
sudo -u "${CRON_USER}" bash -c "
  set -euo pipefail
  cd '${INSTALL_DIR}'
  ${PYTHON} -m venv .venv
  . .venv/bin/activate
  pip install -q --upgrade pip
  pip install -q -r pokemon-pop/scripts/requirements-gemrate.txt
  python -m playwright install chromium
  python -m playwright install-deps chromium
"

echo "==> Log directory"
mkdir -p /var/log/pokepop
chown "${CRON_USER}:${CRON_USER}" /var/log/pokepop

echo "==> Install cron wrapper"
install -m 0755 "${INSTALL_DIR}/pokemon-pop/scripts/vps/run-gemrate-cron.sh" /usr/local/bin/pokepop-gemrate
install -m 0644 "${INSTALL_DIR}/pokemon-pop/scripts/vps/pokepop-gemrate.env.example" /etc/pokepop-gemrate.env.example

echo ""
echo "Done. Next steps:"
echo "  1) cp /etc/pokepop-gemrate.env.example /etc/pokepop-gemrate.env"
echo "  2) Edit /etc/pokepop-gemrate.env (INSTALL_DIR, GIT author, optional deploy key)"
echo "  3) Add GitHub deploy key for ${CRON_USER} (see pokemon-pop/scripts/vps/README.md)"
echo "  4) sudo -u ${CRON_USER} crontab -e"
echo "     Paste line from pokemon-pop/scripts/vps/crontab.example"
echo "  5) Disable .github/workflows/daily-gemrate.yml on GitHub if you stop using Actions"
