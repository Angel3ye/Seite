# 3D Druck Service 🖨️

Ein modernes, privates Auftragsportal für einen 3D-Druck-Service.
Kunden senden über ein Formular einen MakerWorld-Link + Wünsche, erhalten eine
Preisschätzung und einen Auftragscode, mit dem sie den Status verfolgen können.
Ein geschützter Admin-Bereich verwaltet alle Aufträge.

**Tech-Stack:** Next.js 15 · React 18 · Tailwind CSS · shadcn/ui · MongoDB

---

## ✨ Funktionen

- Auftragsformular (Name, MakerWorld-Link, Farbe, Material, Größe, Anzahl, Priorität, Notizen)
- Eingabe von Filament (g) & Druckzeit (Std.) → genaue Preisschätzung
- Automatische Auftragsnummer + Kundencode
- Status-Tracking per Code (ohne Login)
- Admin-Bereich: Aufträge ansehen, Status ändern, bearbeiten, löschen, Fotos hochladen

---

## 🚀 Auf GitHub hochladen & über Vercel veröffentlichen

### Schritt 1 – Projekt zu GitHub hochladen

**Variante A – über die Kommandozeile:**
```bash
cd 3d-druck-service          # entpackter Projektordner
git init
git add .
git commit -m "3D Druck Service"
git branch -M main
git remote add origin https://github.com/DEIN-NAME/DEIN-REPO.git
git push -u origin main
```

**Variante B – über die GitHub-Website:**
1. Auf [github.com](https://github.com) → **New repository** anlegen.
2. „uploading an existing file" wählen und den Projektinhalt hineinziehen.

> ⚠️ Die Datei `.env` wird **absichtlich nicht** hochgeladen (steht in `.gitignore`),
> damit dein Admin-Passwort nicht öffentlich wird. Nutze auf Vercel die
> Umgebungsvariablen (siehe Schritt 3).

### Schritt 2 – MongoDB-Datenbank anlegen (kostenlos)

1. Bei [MongoDB Atlas](https://www.mongodb.com/atlas) ein kostenloses Cluster erstellen.
2. Datenbank-Benutzer (Name + Passwort) anlegen.
3. Unter **Network Access** die IP `0.0.0.0/0` freigeben (erlaubt Zugriff von Vercel).
4. Den **Connection String** kopieren, z. B.
   `mongodb+srv://benutzer:passwort@cluster.mongodb.net`

### Schritt 3 – Bei Vercel deployen

1. Auf [vercel.com](https://vercel.com) einloggen (mit GitHub verbinden).
2. **Add New… → Project** → dein GitHub-Repo auswählen → **Import**.
3. Unter **Environment Variables** folgende Werte eintragen:

   | Name             | Wert (Beispiel)                                        |
   |------------------|--------------------------------------------------------|
   | `MONGO_URL`      | `mongodb+srv://benutzer:passwort@cluster.mongodb.net`  |
   | `DB_NAME`        | `druck_service`                                        |
   | `ADMIN_USERNAME` | `admin`                                                |
   | `ADMIN_PASSWORD` | *(dein sicheres Passwort)*                             |
   | `CORS_ORIGINS`   | `*`                                                    |
   | `FIRECRAWL_API_KEY` | `fc-...` *(optional, für MakerWorld-Auto-Vorschau)* |

4. Auf **Deploy** klicken. Fertig! 🎉
   Vercel baut die App automatisch (`next build`) und vergibt eine öffentliche URL.
   Eine eigene Domain kannst du unter **Settings → Domains** hinzufügen.

> Hinweis: `NEXT_PUBLIC_BASE_URL` wird **nicht** benötigt – die App ruft ihre
> API über relative Pfade (`/api/...`) auf und funktioniert daher unter jeder Domain.

---

## 💻 Lokal entwickeln

```bash
yarn install
cp .env.example .env     # Werte eintragen (lokale MongoDB oder Atlas)
yarn dev                 # http://localhost:3000
```

Produktions-Build testen:
```bash
yarn build && yarn start
```

---

## 🔐 Admin-Zugang

Standard (bitte für den Live-Betrieb über `ADMIN_PASSWORD` ändern):
- Benutzer: `admin`
- Passwort: `Admin123!`

---

## 📁 Wichtige Dateien

```
app/page.js                    # Frontend (Startseite, Status, Admin)
app/layout.js                  # Layout / Dark-Mode
app/globals.css                # Design (dunkel, grüner Akzent)
app/api/[[...path]]/route.js    # Backend (alle API-Endpunkte)
components/ui/                 # UI-Komponenten (shadcn/ui)
```

---

## ⚙️ Erweiterbar

Die App ist bewusst einfach strukturiert und lässt sich leicht ergänzen –
z. B. um weitere Materialien/Farben, mehrere Drucker, E-Mail-Benachrichtigungen
oder ein Bezahlsystem.
