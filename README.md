# 📺 Pluto TV Brasil – Lista M3U para SS IPTV (Com Redirecionador)

Lista otimizada de canais ao vivo do [Pluto TV Brasil](https://pluto.tv/br/watch/live-tv/) em formato M3U, **especificamente adaptada para contornar as limitações de URL do SS IPTV** usando um redirecionador serverless.

## ✨ Características
| Recurso | Descrição |
| --- | --- |
| **Compatibilidade SS IPTV** | Usa URLs curtas via redirecionador (Cloudflare Worker), evitando o truncamento de tokens JWT longos. |
| Atualização automática | A cada 6 horas via GitHub Actions. |
| Persistência inteligente | Canais que param de funcionar não são apagados imediatamente. Só são removidos após 3 atualizações consecutivas com falha. |
| Geo correto (BR) | Usa IP brasileiro + headers adequados para garantir a disponibilidade dos canais. |

## 🔗 Link da lista (raw)
Depois de configurar o redirecionador e deixar o Actions rodar pela primeira vez, use:
```text
https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPOSITORIO/main/pluto_br.m3u