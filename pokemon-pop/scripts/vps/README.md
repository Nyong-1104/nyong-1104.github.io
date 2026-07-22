# Hetzner VPS — daily GemRate PSA

집 PC 없이 **매일 KST 자정쯤** GemRate 세트 페이지를 **1분 간격**으로 가져와 `data/gemrate` + live PSA를 갱신합니다.  
GitHub Actions IP 대신 **Hetzner 전용 IP**로 나갑니다.

## 1. Hetzner에서 서버 만들기

1. [Hetzner Cloud](https://www.hetzner.com/cloud) 가입
2. **Project** 생성 → **Add Server**
3. 추천 스펙:
   - **CPX11** (2 vCPU, 2 GB RAM) — Playwright에 여유
   - Image: **Ubuntu 24.04**
   - Location: **Singapore** (한국에서 SSH 편함) 또는 Helsinki
   - SSH key 등록 (비밀번호 로그인보다 안전)
4. 생성 후 공인 IP로 접속:

```bash
ssh root@YOUR_SERVER_IP
```

## 2. 한 번 설치 (서버에서)

```bash
apt-get update && apt-get install -y git
git clone https://github.com/Nyong-1104/nyong-1104.github.io.git /tmp/pokepop-bootstrap
bash /tmp/pokepop-bootstrap/pokemon-pop/scripts/vps/hetzner-setup.sh
```

또는 repo URL만 바꿀 때:

```bash
REPO_URL=https://github.com/YOUR_USER/YOUR_REPO.git bash hetzner-setup.sh
```

## 3. GitHub push 권한 (deploy key)

VPS가 커밋을 push하려면 **읽기/쓰기 deploy key**가 필요합니다.

1. 서버에서 `pokepop` 유저로 키 생성:

```bash
sudo -u pokepop ssh-keygen -t ed25519 -f /home/pokepop/.ssh/pokepop_deploy -N ""
sudo -u pokepop cat /home/pokepop/.ssh/pokepop_deploy.pub
```

2. GitHub repo → **Settings → Deploy keys → Add deploy key**
   - Title: `hetzner-gemrate`
   - Key: 위 공개키 붙여넣기
   - **Allow write access** 체크

3. `/etc/pokepop-gemrate.env` 설정:

```bash
sudo cp /etc/pokepop-gemrate.env.example /etc/pokepop-gemrate.env
sudo chmod 600 /etc/pokepop-gemrate.env
sudo nano /etc/pokepop-gemrate.env
```

`GIT_SSH_COMMAND` 줄 주석 해제:

```bash
export GIT_SSH_COMMAND='ssh -i /home/pokepop/.ssh/pokepop_deploy -o StrictHostKeyChecking=accept-new'
```

4. 원격 URL을 SSH로 (push용):

```bash
sudo -u pokepop git -C /opt/pokepop remote set-url origin git@github.com:Nyong-1104/nyong-1104.github.io.git
sudo -u pokepop ssh -T git@github.com
```

## 4. cron 등록

```bash
sudo -u pokepop crontab -e
```

`crontab.example` 내용 붙여넣기 (매일 **00:05 KST**).

## 5. 수동 테스트

```bash
sudo -u pokepop POKEPOP_ENV=/etc/pokepop-gemrate.env /usr/local/bin/pokepop-gemrate
tail -f /var/log/pokepop/gemrate-$(date +%Y%m%d).log
```

한 팩만:

```bash
cd /opt/pokepop && . .venv/bin/activate
python pokemon-pop/scripts/fetch_gemrate.py --pack m1l-mega-brave --sleep 60
```

## 6. GitHub Actions와 중복 방지

VPS로 옮기면 **둘 다 돌리면 이중 수집**입니다.

- GitHub → repo → **Actions** → `Daily GemRate PSA` workflow **Disable**
- 또는 `.github/workflows/daily-gemrate.yml` 삭제/주석

시간당 BRG 갱신(`daily-pokepop.yml`)은 그대로 두어도 됩니다. `fetch_live.py`가 기존 GemRate PSA를 유지합니다.

## 비용·운영

- CPX11: 대략 **€4~5/월**
- 트래픽: 하루 Playwright 몇 페이지 수준 → 거의 무시
- 로그: `/var/log/pokepop/`

## 문제 해결

| 증상 | 확인 |
|------|------|
| `playwright install-deps` 실패 | `sudo apt install -y libnss3 libatk1.0-0 ...` 후 재실행 |
| `git push` 거부 | deploy key에 **write** 체크, `remote`가 `git@github.com:...` 인지 |
| Cloudflare 403 | `--sleep` 늘리기 (120), 같은 IP에서 다른 봇 작업 없는지 |
| 메모리 부족 | CPX11(2GB) 이상으로 업그레이드 |
