# 📺 Pluto TV Brasil – Lista M3U para SS IPTV

Gera automaticamente uma lista M3U com os canais ao vivo do [Pluto TV Brasil](https://pluto.tv/br/watch/live-tv/), pensada para o **SS IPTV** em Smart TV (também serve para TiviMate, VLC etc.).

## ❗ Por que a versão antiga não tocava

Cada link trazia dentro dele um token (`jwt=...`) de uma sessão do GitHub Actions, com validade de ~24h e atrelado àquela sessão. Na TV, o link expirava ou era recusado.

## ✅ Como funciona agora

A lista passa a ter **links fixos e sem token**:

```
https://SEU-WORKER.workers.dev/<id-do-canal>.m3u8
```

Quando você abre um canal, um pequeno **Cloudflare Worker** (gratuito, arquivo `worker/worker.js`) cria uma sessão nova no Pluto e redireciona a TV para o stream. O link da lista nunca expira.

## 🚀 Instalação (uma vez só)

**1. Publicar o Worker**
1. Crie uma conta gratuita em [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages → Create → Worker**.
2. Cole o conteúdo de `worker/worker.js`, clique em **Deploy** e copie o endereço (ex.: `https://pluto-br.seunome.workers.dev`).
3. Teste no navegador: abrir `https://pluto-br.seunome.workers.dev/5f120e94a5714d00074576a1.m3u8` deve baixar/redirecionar para um `.m3u8`.

**2. Configurar o GitHub**
1. No repositório: **Settings → Secrets and variables → Actions → aba Variables → New repository variable**.
2. Nome: `PLAY_BASE` · Valor: o endereço do Worker, **sem barra no final**.
3. **Actions → Atualizar lista Pluto TV BR → Run workflow**.

**3. Usar no SS IPTV**

Adicione a lista externa:

```
https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/pluto_br.m3u
```

Sem `PLAY_BASE`, o script volta ao modo antigo (token dentro do link, que expira).

## ⚙️ Persistência de canais

Canais que somem da API só são removidos após **3 atualizações seguidas** (`MAX_FAILS`). O grupo e o número do canal ficam guardados em `state.json`.

## 🛠️ Rodar localmente

```bash
pip install requests
PLAY_BASE=https://pluto-br.seunome.workers.dev python generate_m3u.py
```

## ⚠️ Avisos

- Solução **não oficial**; o conteúdo pertence ao Pluto TV / Paramount. Uso pessoal.
- O Pluto pode alterar a API sem aviso, o que exigiria ajustes no script ou no Worker.
- Alguns canais têm restrição geográfica; o Worker roda na rede da Cloudflare, e a TV acessa o stream a partir da sua própria conexão.

## 📄 Licença

MIT.
