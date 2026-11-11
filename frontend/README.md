# TB-farm React prototype

The React interface is a **standalone, in-memory prototype**, not a replacement for the existing FastAPI application. It does not authenticate users, send email or WhatsApp messages, persist records, upload images, or connect to storage. Refreshing the page resets all changes. Do not use it with real credentials or production data. FastAPI files and its existing routes remain unchanged; an API integration is a separate step.

## Run

```bash
cd frontend
npm ci
npm run dev
```

Open the Vite URL. For a production bundle run `npm run build`; deploy the contents of `dist` with SPA history fallback to `index.html`. Do not expose it as a real authentication system. The Cairo font is bundled locally.

Try `ahmad@example.com`, open the on-screen demo link, and use code `123456`. Registration is also simulated. Use `FARM-DEMO-30` or `FARM-DEMO-365` to preview an active subscription, and `FARM-EXPIRED` to preview its expired state. The footer's Telegram address is a placeholder; replace it with the real developer URL.

## Handoff

- `src/components.tsx` exports typed, reusable UI components; `src/style.css` contains the design tokens and responsive styles.
- `src/i18n.ts` contains both dictionaries. `src/mockData.ts` contains the prototype data and models. `src/main.tsx` holds navigation, mock interactions and local state; replace these interactions with an API adapter before integration. No network calls are made for login, data, or storage.
- Client paths: `/`, `/register`, `/check-email`, `/verify-phone`, `/home`, `/products`, `/sources`, `/sources/new`, `/sources/:id/edit`. Client-side navigation uses the History API; a server serving the build must support fallback for these paths.
- Form names follow the handoff: `email`; `name`, `email`, `phone`, `password`; `code`; `product_id`, `qty_start`, `qty_end`, `money_start`, `money_end`; `name`, `field`, `description`, `phone`, `location`, `img1`–`img4`; `code`, `products_url`, `sources_url`, `sql_api`, `nosql_api`. Input values are positive; signs are displayed by the interface. The prototype uses its own client-side example calculations and validation; the future backend must be authoritative.
- Subscription usage and remaining days are illustrative. Local/cloud dialogs keep only URL origins in memory for display and never contact the supplied endpoints. Do not assume these controls implement storage. Sample source images are generated prototype artwork.
- Production integration must implement authenticated JSON endpoints, session management, validation, authorization, real delivery and storage, error/expiry/attempt-limit handling, CSRF protection as appropriate, and properly configured support links. Never trust the prototype's demo checks.

For a visual component/state gallery open `/components`. The normal screens demonstrate the complete forms, navigation, tables and footer. Run the component checks with `npm test`.
