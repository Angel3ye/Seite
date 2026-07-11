import nodemailer from 'nodemailer'
import { readFileSync } from 'fs'

// .env laden (einfacher Parser)
const env = {}
for (const line of readFileSync('/app/.env', 'utf8').split('\n')) {
  const m = line.match(/^([A-Z0-9_]+)=(.*)$/)
  if (m) {
    let v = m[2].trim()
    if ((v.startsWith("'") && v.endsWith("'")) || (v.startsWith('"') && v.endsWith('"'))) v = v.slice(1, -1)
    env[m[1]] = v
  }
}

const t = nodemailer.createTransport({
  host: env.GMX_SMTP_HOST,
  port: Number(env.GMX_SMTP_PORT),
  secure: Number(env.GMX_SMTP_PORT) === 465,
  requireTLS: Number(env.GMX_SMTP_PORT) !== 465,
  auth: { user: env.GMX_SMTP_USER, pass: env.GMX_SMTP_PASS },
})

try {
  await t.verify()
  console.log('VERIFY_OK')
} catch (e) {
  console.log('VERIFY_FAIL:', e.message)
}
