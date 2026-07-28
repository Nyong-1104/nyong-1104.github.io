# pokePOP game server — 다른 기기와 플레이

PokePop 카드 사이트(GemRate)와 **분리된** 미니게임 전용 실시간 서버입니다.

## 빠른 테스트 (같은 Wi-Fi)

1. 이 PC에 [Node.js LTS](https://nodejs.org) 설치
2. 서버 실행:

```bash
cd pokemon-pop/game/server
npm install
npm start
```

3. Windows 방화벽에서 **포트 3100** 인바운드 허용
4. PC의 랜 IP 확인 (`ipconfig` → IPv4, 예: `192.168.0.12`)
5. 게임 페이지도 **http** 로 열기 (https 페이지에서 http 서버는 브라우저가 막음):

```bash
cd pokemon-pop
python -m http.server 8080
```

6. 이 PC / 다른 기기 브라우저:

- 게임: `http://192.168.0.12:8080/game/?ws=http://192.168.0.12:3100`
- 방 만들기 → 코드 공유 → 다른 기기에서 입장

## 인터넷 (다른 집/모바일 데이터)

GitHub Pages / Vercel(https)에서 쓰려면 서버도 **https/wss** 필요.

추천 예 (도메인 `nyong.app`):

1. 전용 VPS에 Node 서버 설치
2. Nginx + Let’s Encrypt 로 `https://game.nyong.app` → `localhost:3100`
3. 클라이언트:

```text
https://nyong.app/.../game/?ws=https://game.nyong.app
```

서브도메인 이름은 `game`, `play`, `pop` 등 원하는 대로 정하면 됩니다.

## 환경 변수

| 변수 | 기본 | 설명 |
|------|------|------|
| `POKEPOP_GAME_PORT` | `3100` | 서버 포트 |

```bash
POKEPOP_GAME_PORT=3100 npm start
```

## 헬스체크

`GET /health` → `{ ok: true, service: "pokepop-game", rooms: N }`
