import nodemailer from 'nodemailer'

// =============================================================
// GMX SMTP Transporter (serverseitig, wiederverwendet)
// Port 587 -> STARTTLS (secure: false, requireTLS: true)
// Port 465 -> SSL/TLS (secure: true)
// =============================================================
function getTransporter() {
  const host = process.env.GMX_SMTP_HOST || 'mail.gmx.net'
  const port = Number(process.env.GMX_SMTP_PORT || 587)
  const secure = port === 465

  const g = globalThis
  if (!g._gmxTransporter) {
    g._gmxTransporter = nodemailer.createTransport({
      host,
      port,
      secure,
      requireTLS: !secure,
      auth: {
        user: process.env.GMX_SMTP_USER,
        pass: process.env.GMX_SMTP_PASS,
      },
    })
  }
  return g._gmxTransporter
}

function fromHeader() {
  const name = process.env.GMX_FROM_NAME || 'Janniks 3D-Druck Service'
  const email = process.env.GMX_FROM_EMAIL || process.env.GMX_SMTP_USER
  return `"${name}" <${email}>`
}

function isConfigured() {
  return Boolean(process.env.GMX_SMTP_USER && process.env.GMX_SMTP_PASS)
}

function esc(s) {
  return String(s || '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ))
}

// Gemeinsames Mail-Layout (schlicht, dunkel/lila Akzent)
function wrap(title, bodyHtml) {
  return `
  <div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1f2937;">
    <div style="text-align:center;margin-bottom:20px;">
      <span style="font-size:20px;font-weight:700;">Janniks 3D-Druck <span style="color:#8b5cf6;">Service</span></span>
    </div>
    <div style="background:#faf9ff;border:1px solid #ece9f7;border-radius:12px;padding:24px;">
      <h2 style="margin:0 0 12px;font-size:18px;color:#4c1d95;">${title}</h2>
      ${bodyHtml}
    </div>
    <p style="text-align:center;color:#9ca3af;font-size:12px;margin-top:20px;">
      Privates Auftragsportal · nur für Familie, Freunde &amp; Bekannte
    </p>
  </div>`
}

function codeBox(label, value) {
  return `<div style="margin:8px 0;">
    <div style="font-size:12px;color:#6b7280;">${esc(label)}</div>
    <div style="font-size:18px;font-weight:700;letter-spacing:1px;color:#4c1d95;font-family:monospace;">${esc(value)}</div>
  </div>`
}

const eur = (n) => (n == null ? null : `${(Number(n) || 0).toFixed(2).replace('.', ',')} €`)

function linkButton(url, label) {
  if (!url) return ''
  return `<div style="text-align:center;margin:20px 0 4px;">
    <a href="${esc(url)}" style="display:inline-block;background:#8b5cf6;color:#ffffff;text-decoration:none;font-weight:600;padding:12px 22px;border-radius:10px;font-size:14px;">${esc(label)}</a>
  </div>`
}

// =============================================================
// Bestätigung bei Auftragseingang
// =============================================================
export async function sendOrderConfirmationEmail({ to, name, orderNumber, customerCode, trackingUrl }) {
  if (!isConfigured() || !to) return { skipped: true }
  const html = wrap('Dein Auftrag ist eingegangen! 🎉', `
    <p>Hallo ${esc(name)},</p>
    <p>vielen Dank für deinen Druckauftrag. Ich habe ihn erhalten und melde mich, sobald es losgeht. Den Preis trage ich nach Prüfung deines Modells ein – du siehst ihn dann auf der Status-Seite.</p>
    ${codeBox('Auftragsnummer', orderNumber)}
    ${codeBox('Dein Auftragscode (zum Status-Tracking)', customerCode)}
    ${linkButton(trackingUrl, 'Auftragsstatus ansehen')}
    <p style="margin-top:16px;font-size:14px;color:#6b7280;">${trackingUrl ? 'Über den Button oben kommst du direkt zu deinem Auftragsstatus.' : 'Mit dem Auftragscode kannst du jederzeit den aktuellen Status online prüfen.'}</p>
  `)
  const text = `Hallo ${name},\n\nvielen Dank für deinen Druckauftrag – er ist eingegangen.\n\nAuftragsnummer: ${orderNumber}\nDein Auftragscode: ${customerCode}\n${trackingUrl ? `\nStatus ansehen: ${trackingUrl}\n` : ''}\nDen Preis trage ich nach Prüfung deines Modells ein.\n\nJanniks 3D-Druck Service`

  return getTransporter().sendMail({
    from: fromHeader(),
    to,
    subject: `Auftrag eingegangen · ${orderNumber}`,
    text,
    html,
  })
}

// =============================================================
// Benachrichtigung: Auftrag ist abholbereit
// =============================================================
export async function sendPickupReadyEmail({ to, name, orderNumber, customerCode, priceTotal, trackingUrl }) {
  if (!isConfigured() || !to) return { skipped: true }
  const priceStr = eur(priceTotal)
  const html = wrap('Dein Druck ist abholbereit! 📦', `
    <p>Hallo ${esc(name)},</p>
    <p>gute Nachrichten – dein Auftrag ist fertig und <b>abholbereit</b>.</p>
    ${codeBox('Auftragsnummer', orderNumber)}
    ${priceStr ? codeBox('Preis', priceStr) : ''}
    ${codeBox('Dein Auftragscode', customerCode)}
    ${linkButton(trackingUrl, 'Auftragsstatus ansehen')}
    <p style="margin-top:16px;font-size:14px;color:#6b7280;">Melde dich einfach bei mir zur Abholung.</p>
  `)
  const text = `Hallo ${name},\n\ndein Auftrag ist fertig und abholbereit!\n\nAuftragsnummer: ${orderNumber}\n${priceStr ? `Preis: ${priceStr}\n` : ''}Dein Auftragscode: ${customerCode}\n${trackingUrl ? `\nStatus ansehen: ${trackingUrl}\n` : ''}\nMelde dich einfach bei mir zur Abholung.\n\nJanniks 3D-Druck Service`

  return getTransporter().sendMail({
    from: fromHeader(),
    to,
    subject: `Abholbereit · ${orderNumber}`,
    text,
    html,
  })
}

// =============================================================
// Info-Mail an den Betreiber (Jannik) bei neuem Auftrag
// =============================================================
export async function sendAdminNewOrderEmail({ order, trackingUrl }) {
  if (!isConfigured()) return { skipped: true }
  const to = process.env.GMX_FROM_EMAIL || process.env.GMX_SMTP_USER
  if (!to) return { skipped: true }
  const o = order || {}
  const rows = [
    ['Name', o.name],
    ['E-Mail', o.email || '—'],
    ['Auftragsnummer', o.orderNumber],
    ['Auftragscode', o.customerCode],
    ['Farbe', o.color],
    ['Material', o.material],
    ['Größe', o.size != null ? `${o.size} %` : '—'],
    ['Anzahl', o.quantity],
    ['Priorität', o.priority],
    ['MakerWorld', o.makerworldLink],
    ['Notizen', o.notes || '—'],
  ]
  const rowsHtml = rows.map(([k, v]) => `
    <tr>
      <td style="padding:6px 10px;color:#6b7280;font-size:13px;vertical-align:top;white-space:nowrap;">${esc(k)}</td>
      <td style="padding:6px 10px;font-size:13px;color:#1f2937;word-break:break-word;">${esc(v == null ? '' : String(v))}</td>
    </tr>`).join('')
  const html = wrap('Neuer Druckauftrag 🖨️', `
    <p>Es ist ein neuer Auftrag eingegangen:</p>
    <table style="width:100%;border-collapse:collapse;background:#ffffff;border:1px solid #ece9f7;border-radius:8px;overflow:hidden;">${rowsHtml}</table>
    ${linkButton(trackingUrl, 'Auftrag im Status ansehen')}
  `)
  const text = 'Neuer Druckauftrag:\n\n' + rows.map(([k, v]) => `${k}: ${v == null ? '' : v}`).join('\n') + (trackingUrl ? `\n\nStatus: ${trackingUrl}` : '')

  const mailOptions = {
    from: fromHeader(),
    to,
    subject: `Neuer Auftrag · ${o.orderNumber || ''} · ${o.name || ''}`.trim(),
    text,
    html,
  }
  // Reply-To auf die Kunden-E-Mail (falls vorhanden): bessere Zustellung
  // und du kannst direkt aus der Mail heraus dem Kunden antworten.
  if (o.email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(o.email)) {
    mailOptions.replyTo = o.email
  }
  return getTransporter().sendMail(mailOptions)
}

// Verbindung/Anmeldung testen (ohne Mail zu senden)
export async function verifyEmailConnection() {
  if (!isConfigured()) return { ok: false, error: 'SMTP nicht konfiguriert' }
  try {
    await getTransporter().verify()
    return { ok: true }
  } catch (e) {
    return { ok: false, error: String(e?.message || e) }
  }
}
