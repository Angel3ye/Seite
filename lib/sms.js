// =============================================================
// SMS-Versand ueber "SMS Gateway for Android" (Cloud-Modus)
// Doku: https://docs.sms-gate.app
// Endpoint: POST {BASE_URL}/3rdparty/v1/messages (Basic Auth)
// =============================================================

function isConfigured() {
  return Boolean(process.env.SMS_GATEWAY_USERNAME && process.env.SMS_GATEWAY_PASSWORD)
}

function baseUrl() {
  return (process.env.SMS_GATEWAY_BASE_URL || 'https://api.sms-gate.app').replace(/\/$/, '')
}

function authHeader() {
  const u = process.env.SMS_GATEWAY_USERNAME || ''
  const p = process.env.SMS_GATEWAY_PASSWORD || ''
  return 'Basic ' + Buffer.from(`${u}:${p}`).toString('base64')
}

// Telefonnummer nach E.164 normalisieren (Standardland DE = +49)
function normalizePhone(raw) {
  if (!raw) return null
  let s = String(raw).trim().replace(/[\s\-()/.]/g, '')
  if (!s) return null
  if (s.startsWith('+')) return s
  if (s.startsWith('00')) return '+' + s.slice(2)
  const cc = (process.env.SMS_DEFAULT_COUNTRY || 'DE').toUpperCase()
  const prefix = cc === 'DE' ? '49' : cc === 'AT' ? '43' : cc === 'CH' ? '41' : '49'
  if (s.startsWith('0')) return '+' + prefix + s.slice(1)
  // Falls schon ohne fuehrende 0 und ohne + -> Landesvorwahl davor
  return '+' + prefix + s
}

// Kern: eine SMS senden
async function sendSms({ id, to, text }) {
  if (!isConfigured()) return { skipped: true, reason: 'not_configured' }
  const phone = normalizePhone(to)
  if (!phone) return { skipped: true, reason: 'no_phone' }

  const url = baseUrl() + '/3rdparty/v1/messages'
  const res = await fetch(url, {
    method: 'POST',
    headers: { Authorization: authHeader(), 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id,
      phoneNumbers: [phone],
      textMessage: { text },
      simNumber: Number(process.env.SMS_GATEWAY_SIM_NUMBER || 1),
      priority: 100,
      ttl: 3600,
      withDeliveryReport: true,
    }),
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new Error(`SMS-Gateway ${res.status}: ${JSON.stringify(data)}`)
  return { ok: true, data }
}

const SIGN = 'Janniks 3D-Druck'

export function isSmsConfigured() { return isConfigured() }

// (1) Auftragseingang
export async function sendOrderReceivedSms({ orderId, to, name, orderNumber, customerCode, trackingUrl }) {
  const text = `Hallo ${name || ''}, dein Druckauftrag ${orderNumber} ist eingegangen. Code: ${customerCode}.` +
    (trackingUrl ? ` Status: ${trackingUrl}` : '') + ` - ${SIGN}`
  return sendSms({ id: `order:${orderId}:received`, to, text })
}

// (2) Druck startet
export async function sendPrintingStartedSms({ orderId, to, name, orderNumber, trackingUrl }) {
  const text = `Hallo ${name || ''}, dein Auftrag ${orderNumber} wird jetzt gedruckt!` +
    (trackingUrl ? ` Status: ${trackingUrl}` : '') + ` - ${SIGN}`
  return sendSms({ id: `order:${orderId}:printing`, to, text })
}

// (3) Abholbereit
export async function sendReadyForPickupSms({ orderId, to, name, orderNumber, priceTotal, trackingUrl }) {
  const priceStr = priceTotal != null ? ` Preis: ${(Number(priceTotal) || 0).toFixed(2).replace('.', ',')} EUR.` : ''
  const text = `Hallo ${name || ''}, dein Auftrag ${orderNumber} ist abholbereit!${priceStr}` +
    (trackingUrl ? ` Status: ${trackingUrl}` : '') + ` - ${SIGN}`
  return sendSms({ id: `order:${orderId}:ready`, to, text })
}

// Verbindungstest (Anmeldedaten pruefen, ohne SMS zu senden)
export async function verifySmsConnection() {
  if (!isConfigured()) return { ok: false, error: 'SMS-Gateway nicht konfiguriert' }
  try {
    // Auth pruefen ueber Token-Endpoint
    const res = await fetch(baseUrl() + '/3rdparty/v1/auth/token', {
      method: 'POST',
      headers: { Authorization: authHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ ttl: 60, scopes: ['messages:send'] }),
    })
    if (res.status === 401) return { ok: false, error: 'Ungueltige Zugangsdaten (401)' }
    if (res.ok || res.status === 200 || res.status === 201) return { ok: true }
    return { ok: false, error: `Status ${res.status}` }
  } catch (e) {
    return { ok: false, error: String(e?.message || e) }
  }
}
