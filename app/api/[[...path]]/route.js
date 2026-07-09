import { MongoClient } from 'mongodb'
import { v4 as uuidv4 } from 'uuid'
import { NextResponse } from 'next/server'

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
  const MAT_PER_G = 0.03      // Materialkosten pro Gramm
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

async function fetchMakerworldPreview(url) {
  const result = {
    ok: false,
    modelName: null,
    image: null,
    description: null,
    printTime: null,
    filamentGrams: null,
    url,
  }
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

    result.modelName = metaContent(html, 'og:title') || metaContent(html, 'twitter:title')
    result.image = metaContent(html, 'og:image') || metaContent(html, 'twitter:image')
    result.description = metaContent(html, 'og:description') || metaContent(html, 'description')

    // Best-effort: Druckzeit & Filament aus dem HTML/JSON extrahieren
    const timeMatch = html.match(/\"(?:predictionTime|printTime|estimatedTime)\"\s*:\s*(\d+)/i)
    if (timeMatch) {
      const seconds = parseInt(timeMatch[1], 10)
      // Werte koennen in Sekunden oder Minuten vorliegen -> heuristisch in Stunden
      result.printTime = seconds > 10000 ? +(seconds / 3600).toFixed(1) + 'h' : +(seconds / 60).toFixed(1) + 'h'
    }
    const filaMatch = html.match(/\"(?:weight|filamentWeight|materialWeight)\"\s*:\s*([\d.]+)/i)
    if (filaMatch) {
      result.filamentGrams = Math.round(parseFloat(filaMatch[1]))
    }

    result.ok = !!(result.modelName || result.image)
    return result
  } catch (e) {
    return result
  }
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

    // --- Health ---
    if (seg.length === 0) {
      return json({ message: '3D Druck Service API', ok: true })
    }

    // --- MakerWorld Vorschau ---
    if (seg[0] === 'makerworld-preview' && method === 'POST') {
      const body = await request.json().catch(() => ({}))
      if (!body.url) return json({ error: 'Kein Link angegeben' }, 400)
      const preview = await fetchMakerworldPreview(body.url)
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

    // --- Auftrag verfolgen (oeffentlich, per Code) ---
    if (seg[0] === 'orders' && seg[1] === 'track' && method === 'GET') {
      const code = (searchParams.get('code') || '').trim().toUpperCase()
      if (!code) return json({ error: 'Kein Code angegeben' }, 400)
      const order = await orders.findOne({ customerCode: code })
      if (!order) return json({ error: 'Kein Auftrag mit diesem Code gefunden' }, 404)
      // Nur relevante, oeffentliche Felder
      const s = sanitize(order)
      return json({
        orderNumber: s.orderNumber,
        customerCode: s.customerCode,
        name: s.name,
        status: s.status,
        statusHistory: s.statusHistory || [],
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

      const price = calcPrice({
        grams: body.model?.filamentGrams,
        hours: body.model?.printHours,
        size: parseInt(body.size) || 100,
        quantity: parseInt(body.quantity) || 1,
        priority: body.priority || 'Normal',
      })

      const now = new Date().toISOString()
      const order = {
        id: uuidv4(),
        orderNumber: genOrderNumber(),
        customerCode: genCustomerCode(),
        name: body.name,
        makerworldLink: body.makerworldLink,
        color: body.color || 'Egal',
        material: body.material || 'PLA',
        size: parseInt(body.size) || 100,
        quantity: parseInt(body.quantity) || 1,
        priority: body.priority || 'Normal',
        notes: body.notes || '',
        model: body.model || null,   // { modelName, image, description, printTime, filamentGrams, printHours }
        price,
        status: 'Eingegangen',
        statusHistory: [{ status: 'Eingegangen', at: now }],
        photos: [],
        adminNotes: '',
        createdAt: now,
        updatedAt: now,
      }
      await orders.insertOne(order)
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

    // --- ADMIN: Auftrag aktualisieren ---
    if (seg[0] === 'orders' && seg.length === 2 && method === 'PUT') {
      if (!isAuthed(request)) return json({ error: 'Nicht autorisiert' }, 401)
      const id = seg[1]
      const body = await request.json().catch(() => ({}))
      const existing = await orders.findOne({ id })
      if (!existing) return json({ error: 'Auftrag nicht gefunden' }, 404)

      const now = new Date().toISOString()
      const update = { updatedAt: now }
      const allowed = ['status', 'adminNotes', 'notes', 'color', 'material', 'size', 'quantity', 'priority', 'photos', 'model']
      for (const k of allowed) {
        if (body[k] !== undefined) update[k] = body[k]
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
