# Deploy su Cloudflare Workers (non Pages)

Questa guida è per pubblicare il portale **Astro statico** su Cloudflare Workers con asset statici.

## 1) Build locale

```bash
npm ci
npm run build
```

Output: `dist/`.

## 2) Installa Wrangler

```bash
npm install --save-dev wrangler@latest
```

## 3) Crea `wrangler.jsonc`

```json
{
  "$schema": "./node_modules/wrangler/config-schema.json",
  "name": "economia-piemonte",
  "compatibility_date": "2026-03-25",
  "assets": {
    "directory": "./dist",
    "not_found_handling": "404-page"
  }
}
```

> Aggiorna `name` con il nome Worker che vuoi usare.

## 4) Login e deploy

```bash
npx wrangler login
npx wrangler deploy
```

Oppure in un unico comando (build + deploy):

```bash
npx astro build && npx wrangler deploy
```

## 5) Dominio custom in Cloudflare

Dashboard Cloudflare:

1. `Workers & Pages` → seleziona il Worker pubblicato.
2. `Settings` → `Domains & Routes`.
3. Aggiungi il dominio (es. `economia.tuodominio.it`).

## 6) Deploy automatico da GitHub (consigliato)

In Cloudflare, crea un progetto da repository e imposta:

- **Build command**: `npx astro build`
- **Deploy command**: `npx wrangler deploy`

## Note utili

- Questo repository non contiene al momento un file `wrangler.toml/jsonc` versione controllata: va aggiunto una volta definiti nome Worker/account/ambiente.
- Se usi SPA routing, puoi valutare `not_found_handling: "single-page-application"`.
