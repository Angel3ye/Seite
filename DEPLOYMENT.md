# 3D Druck Service – Hosting- & Deployment-Anleitung

Diese App ist eine Standard-**Next.js 15**-Anwendung (React 18 + Tailwind CSS + shadcn/ui)
mit einer **MongoDB**-Datenbank. Du kannst sie überall hosten, wo Node.js läuft.

---

## 1. Was du brauchst

- **Node.js** 18 oder neuer
- **Yarn** (Paketverwaltung)
- Eine **MongoDB-Datenbank** – z. B. kostenlos über [MongoDB Atlas](https://www.mongodb.com/atlas)

---

## 2. Projektstruktur (das Wichtigste)

```
app/
  page.js                    # Komplettes Frontend (Startseite, Status, Admin)
  layout.js                  # Grundgerüst / Dark-Mode
  globals.css                # Design/Farben (grüner Akzent, dunkles Theme)
  api/[[...path]]/route.js    # Komplettes Backend (alle API-Endpunkte)
components/ui/               # UI-Komponenten (shadcn/ui)
package.json                 # Abhängigkeiten
tailwind.config.js           # Design-Konfiguration
.env                         # Umgebungsvariablen (NICHT öffentlich teilen!)
```

---

## 3. Umgebungsvariablen (.env)

Lege beim neuen Host folgende Variablen an (siehe `.env.example`):

| Variable              | Bedeutung                                          | Beispiel                                  |
|-----------------------|----------------------------------------------------|-------------------------------------------|
| `MONGO_URL`           | Verbindungsstring zur MongoDB                      | `mongodb+srv://user:pass@cluster.mongodb.net` |
| `DB_NAME`             | Name der Datenbank                                 | `druck_service`                           |
| `NEXT_PUBLIC_BASE_URL`| Öffentliche Adresse deiner Seite                   | `https://deine-domain.de`                 |
| `ADMIN_USERNAME`      | Admin-Benutzername                                 | `admin`                                   |
| `ADMIN_PASSWORD`      | Admin-Passwort (bitte ändern!)                     | `MeinSicheresPasswort!`                   |
| `CORS_ORIGINS`        | Erlaubte Ursprünge (meist `*`)                     | `*`                                       |

---

## 4. Lokal starten (zum Testen)

```bash
yarn install          # Abhängigkeiten installieren
yarn dev              # Entwicklungsserver auf http://localhost:3000
```

## 5. Produktiv bauen & starten

```bash
yarn build            # Optimierten Build erstellen
yarn start            # Produktionsserver starten (Port 3000)
```

---

## 6. Hosting-Optionen

### Variante A: Vercel (am einfachsten – vom Next.js-Team)
1. Code zu GitHub pushen (in Emergent: Button **„Save to GitHub"** oben rechts).
2. Auf [vercel.com](https://vercel.com) einloggen → **New Project** → dein GitHub-Repo auswählen.
3. Unter **Environment Variables** die Werte aus Abschnitt 3 eintragen.
4. **Deploy** klicken – fertig. Vercel vergibt automatisch eine Adresse (eigene Domain möglich).

### Variante B: Eigener Server / VPS
1. Code auf den Server kopieren.
2. `.env` mit deinen Werten anlegen.
3. `yarn install && yarn build`.
4. `yarn start` (idealerweise über einen Prozessmanager wie **pm2**, damit die App dauerhaft läuft).
5. Optional einen Reverse-Proxy (nginx) für Domain + HTTPS davor setzen.

### Variante C: Railway / Render
- Repo verbinden, Build-Befehl `yarn build`, Start-Befehl `yarn start`, Umgebungsvariablen eintragen.

---

## 7. Datenbank vorbereiten (MongoDB Atlas)

1. Kostenloses Cluster erstellen.
2. Datenbank-Benutzer anlegen (Name + Passwort).
3. Unter **Network Access** deine Server-IP (oder `0.0.0.0/0` für alle) freigeben.
4. Den **Connection String** kopieren und als `MONGO_URL` eintragen.

> Die App legt die benötigte Sammlung `orders` automatisch beim ersten Auftrag an –
> es ist kein manuelles Anlegen von Tabellen nötig.

---

## 8. Wichtiger Sicherheitshinweis

Bevor die Seite öffentlich erreichbar ist, unbedingt **`ADMIN_PASSWORD` ändern**!
Der aktuelle Standard (`Admin123!`) ist nur für die Testphase gedacht.

---

Bei Fragen einfach melden – viel Erfolg mit deinem 3D-Druck-Service! 🖨️
