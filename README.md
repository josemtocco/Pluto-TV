# 📺 Pluto TV Brasil – Lista M3U para SS IPTV

Lista **otimizada** de canais ao vivo do [Pluto TV Brasil](https://pluto.tv/br/watch/live-tv/) em formato M3U, pronta para usar no **SS IPTV**, TiviMate, VLC e qualquer player compatível.

## ✨ Características

| Recurso | Descrição |
|---------|-----------|
| **Atualização automática** | A cada **6 horas** via GitHub Actions |
| **Persistência inteligente** | Canais que param de funcionar **não são apagados imediatamente**. Só são removidos após **3 atualizações consecutivas** com falha |
| **Canais novos** | Incluídos automaticamente assim que aparecem na API do Pluto |
| **Otimizado para SS IPTV** | Tags `tvg-id`, `tvg-logo`, `tvg-chno`, `group-title` corretas |
| **Geo correto (BR)** | Usa IP brasileiro + headers adequados |

## 🔗 Link da lista (raw)

Depois de fazer o **fork** e deixar o Actions rodar pela primeira vez, use:

```
https://raw.githubusercontent.com/SEU_USUARIO/pluto-br-ssiptv/main/pluto_br.m3u
```

Substitua `SEU_USUARIO` pelo seu nome de usuário do GitHub.

## 📲 Como usar no SS IPTV

1. Abra o **SS IPTV**
2. Vá em **Configurações → Listas de reprodução → Adicionar lista**
3. Cole o link raw acima
4. Salve e atualize a lista

Pronto! Os canais aparecerão agrupados por categoria (Filmes, Séries, Infantil, etc.).

## 🚀 Como implantar no seu GitHub (recomendado)

1. Clique em **Fork** neste repositório (ou crie um novo e copie os arquivos)
2. No seu repositório → aba **Actions** → habilite os workflows
3. (Opcional) Clique em **Run workflow** para gerar a lista imediatamente
4. Aguarde ~1 minuto. O arquivo `pluto_br.m3u` será criado/atualizado
5. Use o link raw no SS IPTV

> O workflow roda automaticamente a cada 6 horas. Você também pode disparar manualmente.

## 📁 Estrutura do projeto

```
pluto-br-ssiptv/
├── generate_m3u.py          # Script principal
├── pluto_br.m3u             # Lista gerada (atualizada pelo Actions)
├── state.json               # Estado dos canais (contagem de falhas)
├── .github/workflows/
│   └── update.yml           # Agendamento a cada 6h
└── README.md
```

## ⚙️ Como funciona a persistência

```
Atualização 1 → canal falhou → fails = 1  →  MANTÉM
Atualização 2 → canal falhou → fails = 2  →  MANTÉM
Atualização 3 → canal falhou → fails = 3  →  REMOVE
```

Se o canal voltar a funcionar em qualquer momento, o contador zera.

## 🛠️ Executar localmente

```bash
pip install requests
python generate_m3u.py
```

O arquivo `pluto_br.m3u` será gerado na pasta atual.

## ⚠️ Avisos

- Esta é uma solução **não oficial**. O conteúdo pertence ao Pluto TV / Paramount.
- Os streams usam JWT que expira. Por isso a atualização automática a cada 6h é importante.
- Alguns canais podem ter restrição geográfica (funcionam melhor de dentro do Brasil ou com VPN BR).
- Use apenas para consumo pessoal.

## 📄 Licença

MIT – use livremente.
