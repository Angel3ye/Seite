import { MongoClient } from 'mongodb'
import { v4 as uuidv4 } from 'uuid'
import { NextResponse } from 'next/server'
import { sendOrderConfirmationEmail, sendPickupReadyEmail, sendAdminNewOrderEmail, verifyEmailConnection } from '@/lib/email'

// =============================================================
// MongoDB-Verbindung (serverless-sicher: globale, wiederverwendete
// Verbindung, damit auf Vercel nicht bei jedem Aufruf eine neue
// Verbindung geoeffnet wird)
// =============================================================
async function connectToMongo() {
  if (!process.env.MONGO_URL) {
    throw new Error('MONGO_URL ist nicht gesetzt (Umgebungsvariable fehlt auf dem Server).')
  }
  const g = globalThis
  if (!g._mongoClientPromise) {
    const client = new MongoClient(process.env.MONGO_URL)
    // Bei Verbindungsfehler das (fehlgeschlagene) Promise nicht dauerhaft
    // cachen, damit ein spaeterer Versuch erneut verbinden kann.
    g._mongoClientPromise = client.connect().catch((err) => {
      g._mongoClientPromise = undefined
      throw err
    })
  }
  const client = await g._mongoClientPromise
  // Wenn DB_NAME nicht gesetzt ist, wird die Datenbank aus dem
  // Connection-String verwendet (Fallback: '3d_druck_service').
  return client.db(process.env.DB_NAME || '3d_druck_service')
}

// =============================================================
// CORS-Hilfsfunktion
// =============================================================
function handleCORS(response) {
  response.headers.set('Access-Control-Allow-Origin', process.env.CORS_ORIGINS || '*')
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  response.headers.set('Access-Control-Allow-Credentials', 'true')
  return response
}

function json(data, status = 200) {
  return handleCORS(NextResponse.json(data, { status }))
}

export async function OPTIONS() {
  return handleCORS(new NextResponse(null, { status: 200 }))
}

// =============================================================
// Preisberechnung (serverseitig = verbindliche Schaetzung)
// Preis = Materialkosten + Druckzeit + Verschleiss, dann +20% Gewinn
// =============================================================
function calcPrice({ grams, hours, size = 100, quantity = 1, priority = 'Normal' }) {
  const MAT_PER_G = 0.019     // Materialkosten pro Gramm
  const TIME_PER_H = 1.5      // Druckzeitkosten pro Stunde
  const WEAR = 1.0            // Verschleisspauschale pro Stueck
  const PROFIT = 0.05         // 5% Gewinn auf den Gesamtpreis
  const RUSH = 0.25           // 25% Eilzuschlag

  const qty = Math.max(1, Number(quantity) || 1)
  const s = (Number(size) || 100) / 100
  const baseGrams = Number(grams) > 0 ? Number(grams) : 25   // Standardschaetzung 25g bei 100%
  const baseHours = Number(hours) > 0 ? Number(hours) : 2    // Standardschaetzung 2h bei 100%

  // Material skaliert etwa mit dem Volumen, Zeit eher linear mit der Groesse
  const totalGrams = baseGrams * Math.pow(s, 2.2) * qty
  const totalHours = baseHours * s * qty

  const material = totalGrams * MAT_PER_G
  const time = totalHours * TIME_PER_H
  const wear = WEAR * qty
  const subtotal = material + time + wear
  let total = subtotal * (1 + PROFIT)
  if (priority === 'Eilig') total *= (1 + RUSH)

  const round = (n) => Math.round(n * 100) / 100
  return {
    material: round(material),
    time: round(time),
    wear: round(wear),
    profit: round(total - subtotal),
    subtotal: round(subtotal),
    total: round(total),
    grams: round(totalGrams),
    hours: round(totalHours),
  }
}

// =============================================================
// Authentifizierung (einfaches Token fuer Admin, MVP)
// =============================================================
function expectedToken() {
  const u = process.env.ADMIN_USERNAME || 'admin'
  const p = process.env.ADMIN_PASSWORD || 'Admin123!'
  return Buffer.from(`${u}:${p}`).toString('base64')
}

function isAuthed(request) {
  const auth = request.headers.get('authorization') || ''
  const token = auth.replace(/^Bearer\s+/i, '').trim()
  return token && token === expectedToken()
}

// =============================================================
// MakerWorld-Vorschau: OpenGraph-Meta auslesen (best-effort)
// =============================================================
function decodeEntities(str) {
  if (!str) return str
  return str
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#0?39;/g, "'")
    .replace(/&#x27;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&nbsp;/g, ' ')
}

function metaContent(html, prop) {
  const patterns = [
    new RegExp(`<meta[^>]+(?:property|name)=["']${prop}["'][^>]*content=["']([^"']+)["']`, 'i'),
    new RegExp(`<meta[^>]+content=["']([^"']+)["'][^>]*(?:property|name)=["']${prop}["']`, 'i'),
  ]
  for (const re of patterns) {
    const m = html.match(re)
    if (m && m[1]) return decodeEntities(m[1].trim())
  }
  return null
}

async function fetchMakerworldPreview(url, printer = '') {
  const result = {
    ok: false,
    modelName: null,
    image: null,
    description: null,
    printTime: null,
    printHours: null,
    filamentGrams: null,
    url,
  }

  // Titel von MakerWorld-Zusaetzen befreien
  const cleanTitle = (t) => {
    if (!t) return t
    return t
      .replace(/\s*[-–|]\s*Free 3D Print Model\s*[-–|]\s*MakerWorld\s*$/i, '')
      .replace(/\s*[-–|]\s*MakerWorld\s*$/i, '')
      .trim()
  }

  // 1) Bevorzugt: Firecrawl mit KI-Extraktion (umgeht Cloudflare, rendert JS,
  //    liest Modellname, Beschreibung, Druckzeit & Filament aus dem Druckprofil)
  const key = process.env.FIRECRAWL_API_KEY
  if (key) {
    try {
      const printerHint = printer
        ? `Bevorzuge das Druckprofil fuer den Drucker "${printer}". Wenn dieser Drucker nicht gelistet ist, nimm das erste/Standard-Profil. `
        : 'Nimm das erste/Standard-Druckprofil. '
      const res = await fetch('https://api.firecrawl.dev/v1/scrape', {
        method: 'POST',
        headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          formats: ['json'],
          waitFor: 7000,
          jsonOptions: {
            prompt: `Extrahiere den Modellnamen, eine kurze Beschreibung, die Druckzeit in Stunden (Dezimalzahl) und das gesamte Filamentgewicht in Gramm. ${printerHint}`,
            schema: {
              type: 'object',
              properties: {
                modelName: { type: 'string' },
                description: { type: 'string' },
                printTimeHours: { type: 'number' },
                filamentGrams: { type: 'number' },
              },
            },
          },
        }),
      })
      const data = await res.json()
      const j = (data && data.data && data.data.json) || {}
      const m = (data && data.data && data.data.metadata) || {}
      const title = cleanTitle(j.modelName || m.ogTitle || m.title)
      const image = m.ogImage || null
      if (title || image) {
        result.modelName = title || null
        result.image = image
        result.description = j.description || m.ogDescription || null
        result.printHours = (typeof j.printTimeHours === 'number' && j.printTimeHours > 0)
          ? Math.round(j.printTimeHours * 10) / 10 : null
        result.filamentGrams = (typeof j.filamentGrams === 'number' && j.filamentGrams > 0)
          ? Math.round(j.filamentGrams) : null
        result.printTime = result.printHours ? `${result.printHours} h` : null
        result.ok = true
        return result
      }
    } catch (e) {
      // Faellt unten auf einfachen Abruf zurueck
    }
  }

  // 2) Fallback: einfacher Abruf + OG-Meta (funktioniert oft nicht wegen Cloudflare)
  try {
    const res = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'de,en;q=0.8',
      },
      redirect: 'follow',
    })
    if (!res.ok) return result
    const html = await res.text()

    result.modelName = cleanTitle(metaContent(html, 'og:title') || metaContent(html, 'twitter:title'))
    result.image = metaContent(html, 'og:image') || metaContent(html, 'twitter:image')
    result.description = metaContent(html, 'og:description') || metaContent(html, 'description')

    result.ok = !!(result.modelName || result.image)
    return result
  } catch (e) {
    return result
  }
}

// =============================================================
// Leichtgewichtig: NUR das Vorschaubild + Modellname von MakerWorld
// (bewusst OHNE Gramm/Druckzeit - die bleiben manuelle Eingaben).
// Nutzt Firecrawl-Metadaten (og:image), Fallback: einfacher OG-Abruf.
// =============================================================
async function fetchMakerworldImage(url) {
  const out = { image: null, modelName: null }
  if (!url) return out
  const cleanTitle = (t) => t
    ? t.replace(/\s*[-–|]\s*Free 3D Print Model\s*[-–|]\s*MakerWorld\s*$/i, '')
        .replace(/\s*[-–|]\s*MakerWorld\s*$/i, '').trim()
    : t
  const pickImage = (img) => Array.isArray(img) ? (img[0] || null) : (img || null)

  const key = process.env.FIRECRAWL_API_KEY
  if (key) {
    try {
      const res = await fetch('https://api.firecrawl.dev/v1/scrape', {
        method: 'POST',
        headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, formats: ['markdown'] }),
      })
      const data = await res.json()
      const m = (data && data.data && data.data.metadata) || {}
      const image = pickImage(m.ogImage || m['og:image'])
      const modelName = cleanTitle(m.ogTitle || m.title)
      if (image || modelName) {
        out.image = image
        out.modelName = modelName || null
        return out
      }
    } catch (e) { /* Fallback unten */ }
  }

  // Fallback: einfacher Abruf der OG-Meta (klappt oft nicht wegen Cloudflare)
  try {
    const res = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
      },
      redirect: 'follow',
    })
    if (res.ok) {
      const html = await res.text()
      out.image = metaContent(html, 'og:image') || metaContent(html, 'twitter:image') || null
      out.modelName = cleanTitle(metaContent(html, 'og:title') || metaContent(html, 'twitter:title')) || null
    }
  } catch (e) { /* ignorieren */ }
  return out
}


// =============================================================
// Hilfsfunktionen fuer IDs / Codes
// =============================================================
function genOrderNumber() {
  const n = Math.floor(100000 + Math.random() * 900000)
  return `3D-${n}`
}
function genCustomerCode() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  let s = ''
  for (let i = 0; i < 8; i++) s += chars[Math.floor(Math.random() * chars.length)]
  return s
}

const STATUSES = ['Eingegangen', 'In Pruefung', 'Druck laeuft', 'Fertig', 'Abholbereit', 'Abgeschlossen']

const DEFAULT_MATERIALS = ['PLA', 'PETG', 'TPU']

// Standard-Farben (werden verwendet, solange der Admin keine eigene Liste gespeichert hat)
const DEFAULT_COLORS = [
  { name: 'Schwarz', hex: '#1a1a1a' },
  { name: 'Weiss', hex: '#f5f5f5' },
  { name: 'Grau', hex: '#8a8a8a' },
  { name: 'Rot', hex: '#e11d48' },
  { name: 'Blau', hex: '#2563eb' },
  { name: 'Gruen', hex: '#16a34a' },
  { name: 'Gelb', hex: '#facc15' },
  { name: 'Orange', hex: '#f97316' },
  { name: 'Silber', hex: '#c0c0c0' },
  { name: 'Gold', hex: '#d4af37' },
]

function sanitize(order) {
  if (!order) return order
  const { _id, ...rest } = order
  return rest
}

// =============================================================
// Haupt-Handler
// =============================================================
async function handler(request) {
  const { pathname, searchParams } = request.nextUrl
  // Pfad nach /api
  const path = pathname.replace(/^\/api\/?/, '')
  const seg = path.split('/').filter(Boolean)
  const method = request.method

  try {
    const database = await connectToMongo()
    const orders = database.collection('orders')
    const settings = database.collection('settings')

    // --- Health ---
    if (seg.length === 0) {
      return json({ message: '3D Druck Service API', ok: true })
    }

    // --- Farben abrufen (oeffentlich) ---
    if (seg[0] === 'colors' && method === 'GET') {
      const doc = await settings.findOne({ key: 'colors' })
      const colors = (doc && Array.isArray(doc.value) && doc.value.length > 0) ? doc.value : DEFAULT_COLORS
      return json({ colors })
    }

    // --- Farben speichern (Admin) ---
    if (seg[0] === 'settings' && seg[1] === 'colors' && method === 'PUT') {
      if (!isAuthed(request)) return json({ error: 'Nicht autorisiert' }, 401)
      const body = await request.json().catch(() => ({}))
      const colors = Array.isArray(body.colors)
        ? body.colors
            .filter((c) => c && typeof c.name === 'string' && c.name.trim())
            .map((c) => ({ name: c.name.trim(), hex: c.hex || '#888888' }))
        : []
      await settings.updateOne(
        { key: 'colors' },
        { $set: { key: 'colors', value: colors, updatedAt: new Date().toISOString() } },
        { upsert: true }
      )
      return json({ ok: true, colors })
    }

    // --- Materialien abrufen (oeffentlich) ---
    if (seg[0] === 'materials' && method === 'GET') {
      const doc = await settings.findOne({ key: 'materials' })
      const materials = (doc && Array.isArray(doc.value) && doc.value.length > 0) ? doc.value : DEFAULT_MATERIALS
      return json({ materials })
    }

    // --- Materialien speichern (Admin) ---
    if (seg[0] === 'settings' && seg[1] === 'materials' && method === 'PUT') {
      if (!isAuthed(request)) return json({ error: 'Nicht autorisiert' }, 401)
      const body = await request.json().catch(() => ({}))
      const materials = Array.isArray(body.materials)
        ? [...new Set(body.materials.filter((m) => typeof m === 'string' && m.trim()).map((m) => m.trim()))]
        : []
      await settings.updateOne(
        { key: 'materials' },
        { $set: { key: 'materials', value: materials, updatedAt: new Date().toISOString() } },
        { upsert: true }
      )
      return json({ ok: true, materials })
    }

    // --- Drucker-Einstellung abrufen (Admin) ---
    if (seg[0] === 'settings' && seg[1] === 'printer' && method === 'GET') {
      if (!isAuthed(request)) return json({ error: 'Nicht autorisiert' }, 401)
      const doc = await settings.findOne({ key: 'printer' })
      return json({ printer: (doc && doc.value) || '' })
    }

    // --- Drucker-Einstellung speichern (Admin) ---
    if (seg[0] === 'settings' && seg[1] === 'printer' && method === 'PUT') {
      if (!isAuthed(request)) return json({ error: 'Nicht autorisiert' }, 401)
      const body = await request.json().catch(() => ({}))
      const printer = typeof body.printer === 'string' ? body.printer.trim() : ''
      await settings.updateOne(
        { key: 'printer' },
        { $set: { key: 'printer', value: printer, updatedAt: new Date().toISOString() } },
        { upsert: true }
      )
      return json({ ok: true, printer })
    }

    // --- MakerWorld Vorschau ---
    if (seg[0] === 'makerworld-preview' && method === 'POST') {
      const body = await request.json().catch(() => ({}))
      if (!body.url) return json({ error: 'Kein Link angegeben' }, 400)
      const pdoc = await settings.findOne({ key: 'printer' })
      const printer = (pdoc && pdoc.value) || process.env.DEFAULT_PRINTER || ''
      const preview = await fetchMakerworldPreview(body.url, printer)
      return json(preview)
    }

    // --- Preis-Vorschau (ohne speichern) ---
    if (seg[0] === 'price-preview' && method === 'POST') {
      const body = await request.json().catch(() => ({}))
      return json(calcPrice(body))
    }

    // --- Admin Login ---
    if (seg[0] === 'admin' && seg[1] === 'login' && method === 'POST') {
      const body = await request.json().catch(() => ({}))
      const u = process.env.ADMIN_USERNAME || 'admin'
      const p = process.env.ADMIN_PASSWORD || 'Admin123!'
      if (body.username === u && body.password === p) {
        return json({ token: expectedToken(), username: u })
      }
      return json({ error: 'Benutzername oder Passwort ist falsch' }, 401)
    }

    // --- E-Mail-Verbindung testen (Admin) ---
    if (seg[0] === 'email-status' && method === 'GET') {
      if (!isAuthed(request)) return json({ error: 'Nicht autorisiert' }, 401)
      const result = await verifyEmailConnection()
      return json(result)
    }

    // --- Auftrag verfolgen (oeffentlich, per Code) ---
    if (seg[0] === 'orders' && seg[1] === 'track' && method === 'GET') {
      const code = (searchParams.get('code') || '').trim().toUpperCase()
      if (!code) return json({ error: 'Kein Code angegeben' }, 400)
      const order = await orders.findOne({ customerCode: code })
      if (!order) return json({ error: 'Kein Auftrag mit diesem Code gefunden' }, 404)
      // Nur relevante, oeffentliche Felder
      const s = sanitize(order)
      // Warteschlange: wie viele noch offene Auftraege wurden frueher erstellt?
      const doneSet = new Set(['Fertig', 'Abholbereit', 'Abgeschlossen'])
      let queueAhead = 0
      if (!doneSet.has(s.status)) {
        const all = await orders.find({}).toArray()
        queueAhead = all.filter((o) =>
          o.id !== s.id && !doneSet.has(o.status) && new Date(o.createdAt) < new Date(s.createdAt)
        ).length
      }
      return json({
        orderNumber: s.orderNumber,
        customerCode: s.customerCode,
        name: s.name,
        status: s.status,
        statusHistory: s.statusHistory || [],
        customerMessage: s.customerMessage || '',
        queueAhead,
        model: s.model || null,
        makerworldLink: s.makerworldLink,
        color: s.color,
        material: s.material,
        size: s.size,
        quantity: s.quantity,
        priority: s.priority,
        price: s.price,
        photos: s.photos || [],
        createdAt: s.createdAt,
        updatedAt: s.updatedAt,
      })
    }

    // --- Auftrag erstellen (oeffentlich) ---
    if (seg[0] === 'orders' && seg.length === 1 && method === 'POST') {
      const body = await request.json().catch(() => ({}))
      if (!body.name || !body.makerworldLink) {
        return json({ error: 'Name und MakerWorld-Link sind erforderlich' }, 400)
      }

      const now = new Date().toISOString()

      // Vorschaubild + Modellname von MakerWorld laden (best effort, max. 12s).
      // Gramm/Druckzeit + Preis werden spaeter vom Admin eingetragen.
      let fetchedImg = { image: null, modelName: null }
      try {
        fetchedImg = await Promise.race([
          fetchMakerworldImage(body.makerworldLink),
          new Promise((r) => setTimeout(() => r({ image: null, modelName: null }), 12000)),
        ])
      } catch (e) { /* ignorieren */ }
      const model = {
        ...(body.model || {}),
        ...(fetchedImg.image ? { image: fetchedImg.image } : {}),
        ...(fetchedImg.modelName ? { modelName: fetchedImg.modelName } : {}),
      }

      const order = {
        id: uuidv4(),
        orderNumber: genOrderNumber(),
        customerCode: genCustomerCode(),
        name: body.name,
        email: typeof body.email === 'string' ? body.email.trim() : '',
        makerworldLink: body.makerworldLink,
        color: body.color || 'Egal',
        material: body.material || 'PLA',
        size: parseInt(body.size) || 100,
        quantity: parseInt(body.quantity) || 1,
        priority: body.priority || 'Normal',
        notes: body.notes || '',
        model: Object.keys(model).length ? model : null,   // { modelName, image, filamentGrams, printHours }
        price: null,   // wird vom Admin nach Pruefung (Gramm/Zeit) berechnet
        status: 'Eingegangen',
        statusHistory: [{ status: 'Eingegangen', at: now }],
        photos: [],
        adminNotes: '',
        createdAt: now,
        updatedAt: now,
      }
      await orders.insertOne(order)

      // Direkter Link zur Status-Seite (mit vorausgefuelltem Code)
      const baseUrl = (process.env.NEXT_PUBLIC_BASE_URL || '').replace(/\/$/, '')
      const trackingUrl = baseUrl ? `${baseUrl}/?track=${order.customerCode}` : ''

      // Bestätigungs-Mail an den Kunden (best effort)
      if (order.email) {
        sendOrderConfirmationEmail({
          to: order.email,
          name: order.name,
          orderNumber: order.orderNumber,
          customerCode: order.customerCode,
          trackingUrl,
        }).catch((err) => console.error('E-Mail (Bestätigung) fehlgeschlagen:', err?.message || err))
      }

      // Info-Mail an den Betreiber (Jannik) mit den wichtigsten Daten (best effort)
      sendAdminNewOrderEmail({
        order,
        trackingUrl,
      }).catch((err) => console.error('E-Mail (Admin-Info) fehlgeschlagen:', err?.message || err))

      return json({
        ok: true,
        orderNumber: order.orderNumber,
        customerCode: order.customerCode,
        price: order.price,
      })
    }

    // --- ADMIN: alle Auftraege auflisten ---
    if (seg[0] === 'orders' && seg.length === 1 && method === 'GET') {
      if (!isAuthed(request)) return json({ error: 'Nicht autorisiert' }, 401)
      const all = await orders.find({}).sort({ createdAt: -1 }).toArray()
      return json({ orders: all.map(sanitize) })
    }

    // --- ADMIN: Vorschaubild (neu) laden ---
    if (seg[0] === 'orders' && seg.length === 3 && seg[2] === 'fetch-image' && method === 'POST') {
      if (!isAuthed(request)) return json({ error: 'Nicht autorisiert' }, 401)
      const id = seg[1]
      const existing = await orders.findOne({ id })
      if (!existing) return json({ error: 'Auftrag nicht gefunden' }, 404)
      const fetched = await fetchMakerworldImage(existing.makerworldLink)
      if (!fetched.image) return json({ ok: false, error: 'Kein Bild gefunden' })
      const model = {
        ...(existing.model || {}),
        image: fetched.image,
        ...(fetched.modelName ? { modelName: fetched.modelName } : {}),
      }
      await orders.updateOne({ id }, { $set: { model, updatedAt: new Date().toISOString() } })
      const updated = await orders.findOne({ id })
      return json({ ok: true, order: sanitize(updated) })
    }

    // --- ADMIN: Auftrag aktualisieren ---
    if (seg[0] === 'orders' && seg.length === 2 && method === 'PUT') {
      if (!isAuthed(request)) return json({ error: 'Nicht autorisiert' }, 401)
      const id = seg[1]
      const body = await request.json().catch(() => ({}))
      const existing = await orders.findOne({ id })
      if (!existing) return json({ error: 'Auftrag nicht gefunden' }, 404)

      const now = new Date().toISOString()
      const update = { updatedAt: now }
      const allowed = ['status', 'adminNotes', 'notes', 'color', 'material', 'size', 'quantity', 'priority', 'photos', 'customerMessage', 'email']
      for (const k of allowed) {
        if (body[k] !== undefined) update[k] = body[k]
      }
      
      // Merge model fields (preserve existing image/modelName when setting grams/hours)
      if (body.model !== undefined) {
        update.model = { ...(existing.model || {}), ...body.model }
      }

      // Statusverlauf pflegen
      let history = existing.statusHistory || []
      if (body.status && body.status !== existing.status) {
        history = [...history, { status: body.status, at: now }]
        update.statusHistory = history
      }

      // Preis neu berechnen, falls preisrelevante Felder geaendert wurden
      if (['size', 'quantity', 'priority', 'model'].some((k) => body[k] !== undefined)) {
        const model = body.model !== undefined ? body.model : existing.model
        update.price = calcPrice({
          grams: model?.filamentGrams,
          hours: model?.printHours,
          size: body.size !== undefined ? parseInt(body.size) : existing.size,
          quantity: body.quantity !== undefined ? parseInt(body.quantity) : existing.quantity,
          priority: body.priority !== undefined ? body.priority : existing.priority,
        })
      }

      await orders.updateOne({ id }, { $set: update })
      const updated = await orders.findOne({ id })

      // Abhol-Mail: nur wenn Status NEU auf "Abholbereit" wechselt
      if (
        body.status === 'Abholbereit' &&
        existing.status !== 'Abholbereit' &&
        updated?.email
      ) {
        sendPickupReadyEmail({
          to: updated.email,
          name: updated.name,
          orderNumber: updated.orderNumber,
          customerCode: updated.customerCode,
          priceTotal: updated.price?.total ?? null,
          trackingUrl: (() => {
            const b = (process.env.NEXT_PUBLIC_BASE_URL || '').replace(/\/$/, '')
            return b ? `${b}/?track=${updated.customerCode}` : ''
          })(),
        }).catch((err) => console.error('E-Mail (Abholbereit) fehlgeschlagen:', err?.message || err))
      }

      return json({ ok: true, order: sanitize(updated) })
    }

    // --- ADMIN: Auftrag loeschen ---
    if (seg[0] === 'orders' && seg.length === 2 && method === 'DELETE') {
      if (!isAuthed(request)) return json({ error: 'Nicht autorisiert' }, 401)
      const id = seg[1]
      const r = await orders.deleteOne({ id })
      if (r.deletedCount === 0) return json({ error: 'Auftrag nicht gefunden' }, 404)
      return json({ ok: true })
    }

    return json({ error: 'Route nicht gefunden' }, 404)
  } catch (e) {
    console.error('API-Fehler:', e)
    return json({ error: 'Serverfehler', detail: String(e?.message || e) }, 500)
  }
}

export const GET = handler
export const POST = handler
export const PUT = handler
export const DELETE = handler
