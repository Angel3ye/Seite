'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { motion, AnimatePresence, MotionConfig } from 'framer-motion'
import {
  Printer, Package, Search, ShieldCheck, LogOut, Trash2, Pencil, Upload,
  Loader2, CheckCircle2, Copy, Clock, Weight, Boxes, Zap, ExternalLink,
  Sparkles, ClipboardList, RefreshCw, X, ImageIcon, Send, Home as HomeIcon
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem
} from '@/components/ui/select'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from '@/components/ui/dialog'
import { Toaster } from '@/components/ui/sonner'
import { toast } from 'sonner'

// =============================================================
// Konstanten / Stammdaten
// =============================================================
const COLORS = [
  { name: 'Schwarz', hex: '#1a1a1a' },
  { name: 'Weiß', hex: '#f5f5f5' },
  { name: 'Grau', hex: '#8a8a8a' },
  { name: 'Rot', hex: '#e11d48' },
  { name: 'Blau', hex: '#2563eb' },
  { name: 'Grün', hex: '#16a34a' },
  { name: 'Gelb', hex: '#facc15' },
  { name: 'Orange', hex: '#f97316' },
  { name: 'Silber', hex: '#c0c0c0' },
  { name: 'Gold', hex: '#d4af37' },
  { name: 'Transparent', hex: 'linear-gradient(135deg,#e0e0e0,#ffffff)' },
  { name: 'Egal / Überrasch mich', hex: 'linear-gradient(135deg,#16a34a,#2563eb)' },
]
const MATERIALS = ['PLA', 'PETG', 'TPU']
const SIZES = [50, 75, 100, 125, 150, 200]
const PRIORITIES = ['Normal', 'Eilig']
const STATUS_STEPS = ['Eingegangen', 'In Prüfung', 'Druck läuft', 'Fertig', 'Abholbereit', 'Abgeschlossen']

const STATUS_STYLES = {
  'Eingegangen': 'bg-slate-500/20 text-slate-300 border-slate-500/40',
  'In Prüfung': 'bg-amber-500/20 text-amber-300 border-amber-500/40',
  'Druck läuft': 'bg-blue-500/20 text-blue-300 border-blue-500/40',
  'Fertig': 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
  'Abholbereit': 'bg-primary/20 text-primary border-primary/40',
  'Abgeschlossen': 'bg-emerald-600/20 text-emerald-300 border-emerald-600/40',
}

// =============================================================
// Preisberechnung (Client-Live-Vorschau, identisch zum Server)
// =============================================================
function calcPrice({ grams, hours, size = 100, quantity = 1, priority = 'Normal' }) {
  const MAT_PER_G = 0.03, TIME_PER_H = 2.0, WEAR = 1.5, PROFIT = 0.20, RUSH = 0.25
  const qty = Math.max(1, Number(quantity) || 1)
  const s = (Number(size) || 100) / 100
  const baseGrams = Number(grams) > 0 ? Number(grams) : 25
  const baseHours = Number(hours) > 0 ? Number(hours) : 2
  const totalGrams = baseGrams * Math.pow(s, 2.2) * qty
  const totalHours = baseHours * s * qty
  const material = totalGrams * MAT_PER_G
  const time = totalHours * TIME_PER_H
  const wear = WEAR * qty
  const subtotal = material + time + wear
  let total = subtotal * (1 + PROFIT)
  if (priority === 'Eilig') total *= (1 + RUSH)
  const r = (n) => Math.round(n * 100) / 100
  return { material: r(material), time: r(time), wear: r(wear), subtotal: r(subtotal), total: r(total) }
}

const eur = (n) => `${(Number(n) || 0).toFixed(2).replace('.', ',')} €`

// =============================================================
// Header / Navigation
// =============================================================
function Header({ view, setView }) {
  const nav = [
    { key: 'home', label: 'Startseite', icon: HomeIcon },
    { key: 'track', label: 'Status prüfen', icon: Search },
    { key: 'admin', label: 'Admin', icon: ShieldCheck },
  ]
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 backdrop-blur-xl bg-background/70">
      <div className="container flex h-16 items-center justify-between">
        <button onClick={() => setView('home')} className="flex items-center gap-2.5 group">
          <div className="grid place-items-center h-9 w-9 rounded-xl bg-gradient-to-br from-primary to-accent shadow-lg shadow-primary/20">
            <Printer className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="font-bold text-lg tracking-tight">Janniks 3D-Druck <span className="text-primary">Service</span></span>
        </button>
        <nav className="flex items-center gap-1">
          {nav.map((n) => (
            <Button
              key={n.key}
              variant={view === n.key ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setView(n.key)}
              className="gap-1.5"
            >
              <n.icon className="h-4 w-4" />
              <span className="hidden sm:inline">{n.label}</span>
            </Button>
          ))}
        </nav>
      </div>
    </header>
  )
}

// =============================================================
// MakerWorld-Vorschau-Karte
// =============================================================
function PreviewCard({ preview, loading }) {
  if (loading) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin text-primary" />
        Lade Modellinformationen von MakerWorld…
      </div>
    )
  }
  if (!preview) return null
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className="overflow-hidden rounded-xl border border-primary/30 bg-primary/5"
    >
      <div className="flex flex-col sm:flex-row gap-4 p-4">
        <div className="h-40 w-full sm:w-40 shrink-0 overflow-hidden rounded-lg bg-muted grid place-items-center">
          {preview.image ? (
            <img src={preview.image} alt={preview.modelName || 'Modell'} className="h-full w-full object-cover" />
          ) : (
            <ImageIcon className="h-10 w-10 text-muted-foreground" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-xs font-medium text-primary">Vorschau</span>
          </div>
          <h4 className="font-semibold truncate">{preview.modelName || 'Unbekanntes Modell'}</h4>
          {preview.description && (
            <p className="mt-1 text-sm text-muted-foreground line-clamp-3">{preview.description}</p>
          )}
          <div className="mt-3 flex flex-wrap gap-2">
            {preview.printTime && (
              <Badge variant="secondary" className="gap-1"><Clock className="h-3 w-3" />{preview.printTime}</Badge>
            )}
            {preview.filamentGrams && (
              <Badge variant="secondary" className="gap-1"><Weight className="h-3 w-3" />{preview.filamentGrams} g</Badge>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// =============================================================
// Startseite: Begrüßung + Auftragsformular
// =============================================================
function HomeView({ setView, setLastOrder }) {
  const [form, setForm] = useState({
    name: '', makerworldLink: '', color: 'Egal / Überrasch mich',
    material: 'PLA', size: 100, quantity: 1, priority: 'Normal', notes: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [manual, setManual] = useState({ grams: '', hours: '' })

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const hasDetails = !!(manual.grams || manual.hours)

  const price = useMemo(() => calcPrice({
    grams: manual.grams, hours: manual.hours,
    size: form.size, quantity: form.quantity, priority: form.priority,
  }), [manual.grams, manual.hours, form.size, form.quantity, form.priority])

  const submit = async () => {
    if (!form.name.trim()) return toast.error('Bitte gib deinen Namen an.')
    if (!/^https?:\/\//i.test(form.makerworldLink)) return toast.error('Bitte gib einen gültigen MakerWorld-Link an.')
    setSubmitting(true)
    try {
      const model = (manual.grams || manual.hours)
        ? {
            manual: true,
            filamentGrams: Number(manual.grams) || undefined,
            printHours: Number(manual.hours) || undefined,
          }
        : null
      const res = await fetch('/api/orders', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, model }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Fehler')
      setLastOrder({ orderNumber: data.orderNumber, customerCode: data.customerCode, price: data.price })
    } catch (e) {
      toast.error(e.message || 'Auftrag konnte nicht gesendet werden.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="container py-10 max-w-3xl">
      {/* Hero / Begrüßung */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm text-primary mb-5">
          <Sparkles className="h-4 w-4" /> Privates Auftragsportal
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">
          Willkommen bei meinem <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">3D-Druck-Service</span>
        </h1>
        <p className="text-muted-foreground text-lg leading-relaxed max-w-2xl mx-auto">
          Hier kannst du mir ganz einfach einen Druckauftrag senden. Suche dir auf MakerWorld ein Modell aus,
          kopiere den Link und sende ihn mir.
        </p>
        <div className="mt-6">
          <a href="https://makerworld.com/de/3d-models" target="_blank" rel="noreferrer">
            <Button variant="secondary" size="lg" className="gap-2">
              <ExternalLink className="h-4 w-4" /> Modelle auf MakerWorld entdecken
            </Button>
          </a>
        </div>
      </motion.div>

      {/* Formular */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <Card className="glass-card border-border/60 shadow-2xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><ClipboardList className="h-5 w-5 text-primary" /> Druckauftrag</CardTitle>
            <CardDescription>Fülle die Felder aus – der Schätzpreis wird automatisch berechnet.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Name */}
            <div className="space-y-2">
              <Label>Name</Label>
              <Input placeholder="Dein Name" value={form.name} onChange={(e) => set('name', e.target.value)} />
            </div>

            {/* MakerWorld-Link */}
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <Label>MakerWorld-Link</Label>
                <a href="https://makerworld.com/de/3d-models" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-accent hover:underline">
                  <ExternalLink className="h-3 w-3" /> Modelle durchsuchen
                </a>
              </div>
              <Input
                placeholder="https://makerworld.com/de/models/..."
                value={form.makerworldLink}
                onChange={(e) => set('makerworldLink', e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Füge einfach den MakerWorld-Link ein – er wird gespeichert.</p>
              <div className="grid sm:grid-cols-2 gap-3 rounded-lg border border-border bg-muted/20 p-3">
                <div className="sm:col-span-2 text-xs font-medium text-muted-foreground">Filament &amp; Druckzeit (von der MakerWorld-Seite)</div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Filament in g</Label>
                  <Input type="number" min={0} placeholder="z. B. 45" value={manual.grams} onChange={(e) => setManual((m) => ({ ...m, grams: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Druckzeit in Std.</Label>
                  <Input type="number" min={0} step="0.5" placeholder="z. B. 3" value={manual.hours} onChange={(e) => setManual((m) => ({ ...m, hours: e.target.value }))} />
                </div>
                <div className="sm:col-span-2 text-xs text-muted-foreground">Diese Werte findest du direkt auf der MakerWorld-Seite. Trägst du sie ein, wird der Preis genau berechnet.</div>
              </div>
            </div>

            {/* Farbe + Material */}
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Wunschfarbe</Label>
                <Select value={form.color} onValueChange={(v) => set('color', v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {COLORS.map((c) => (
                      <SelectItem key={c.name} value={c.name}>
                        <span className="flex items-center gap-2">
                          <span className="h-4 w-4 rounded-full border border-border" style={{ background: c.hex }} />
                          {c.name}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Material</Label>
                <Select value={form.material} onValueChange={(v) => set('material', v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {MATERIALS.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Größe + Anzahl */}
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Größe (Skalierung)</Label>
                <Select value={String(form.size)} onValueChange={(v) => set('size', parseInt(v))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {SIZES.map((s) => <SelectItem key={s} value={String(s)}>{s} %</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Anzahl</Label>
                <Input type="number" min={1} value={form.quantity} onChange={(e) => set('quantity', Math.max(1, parseInt(e.target.value) || 1))} />
              </div>
            </div>

            {/* Priorität */}
            <div className="space-y-2">
              <Label>Priorität</Label>
              <div className="flex gap-3">
                {PRIORITIES.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => set('priority', p)}
                    className={`flex-1 rounded-lg border px-4 py-3 text-sm font-medium transition-all ${
                      form.priority === p
                        ? 'border-primary bg-primary/15 text-primary'
                        : 'border-border bg-muted/20 text-muted-foreground hover:border-primary/40'
                    }`}
                  >
                    <span className="flex items-center justify-center gap-2">
                      {p === 'Eilig' ? <Zap className="h-4 w-4" /> : <Clock className="h-4 w-4" />}
                      {p}{p === 'Eilig' ? ' (+25%)' : ''}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Notizen */}
            <div className="space-y-2">
              <Label>Notizen</Label>
              <Textarea placeholder="Besondere Wünsche, z. B. bestimmte Farbnuance, Verwendungszweck…" value={form.notes} onChange={(e) => set('notes', e.target.value)} />
            </div>

            <Separator />

            {/* Preisvorschlag */}
            <div className="rounded-xl border border-primary/30 bg-gradient-to-br from-primary/10 to-accent/5 p-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-muted-foreground">Geschätzter Preis</div>
                  <div className="text-3xl font-bold text-primary">ca. {eur(price.total)}</div>
                </div>
                <Package className="h-10 w-10 text-primary/50" />
              </div>
              <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                <div className="rounded-md bg-background/40 p-2 text-center">Material<br /><span className="text-foreground font-medium">{eur(price.material)}</span></div>
                <div className="rounded-md bg-background/40 p-2 text-center">Druckzeit<br /><span className="text-foreground font-medium">{eur(price.time)}</span></div>
                <div className="rounded-md bg-background/40 p-2 text-center">Verschleiß<br /><span className="text-foreground font-medium">{eur(price.wear)}</span></div>
              </div>
              <p className="mt-3 text-xs text-muted-foreground">{hasDetails ? '' : 'Grobe Schätzung ohne genaue Modelldaten (Standardannahme ~25 g / 2 Std.). '}Der endgültige Preis wird nach Prüfung des Modells bestätigt.</p>
            </div>

            <Button className="w-full gap-2 h-12 text-base" onClick={submit} disabled={submitting}>
              {submitting ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
              Auftrag absenden
            </Button>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

// =============================================================
// Erfolgs-Dialog nach Absenden
// =============================================================
function SuccessDialog({ order, onClose, goTrack }) {
  if (!order) return null
  const copy = (t) => { navigator.clipboard.writeText(t); toast.success('Kopiert!') }
  return (
    <Dialog open={!!order} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="mx-auto mb-2 grid place-items-center h-14 w-14 rounded-full bg-primary/15">
            <CheckCircle2 className="h-8 w-8 text-primary" />
          </div>
          <DialogTitle className="text-center text-xl">Vielen Dank!</DialogTitle>
          <DialogDescription className="text-center">
            Dein Auftrag wurde erfolgreich übermittelt. Ich melde mich schnellstmöglich bei dir.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="rounded-lg border border-border bg-muted/30 p-4">
            <div className="text-xs text-muted-foreground">Auftragsnummer</div>
            <div className="font-mono font-semibold">{order.orderNumber}</div>
          </div>
          <div className="rounded-lg border border-primary/40 bg-primary/10 p-4">
            <div className="text-xs text-muted-foreground">Dein Auftragscode – damit prüfst du den Status</div>
            <div className="flex items-center justify-between">
              <div className="font-mono text-2xl font-bold tracking-widest text-primary">{order.customerCode}</div>
              <Button size="icon" variant="ghost" onClick={() => copy(order.customerCode)}><Copy className="h-4 w-4" /></Button>
            </div>
          </div>
          <div className="text-center text-sm text-muted-foreground">Geschätzter Preis: <span className="text-primary font-semibold">ca. {eur(order.price?.total)}</span></div>
        </div>
        <DialogFooter className="sm:justify-center gap-2">
          <Button variant="secondary" onClick={onClose}>Schließen</Button>
          <Button onClick={goTrack} className="gap-2"><Search className="h-4 w-4" /> Status prüfen</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// =============================================================
// Status-Tracking (öffentlich)
// =============================================================
function StatusStepper({ status }) {
  const idx = STATUS_STEPS.indexOf(status)
  return (
    <div className="space-y-1">
      {STATUS_STEPS.map((s, i) => {
        const done = i <= idx
        const active = i === idx
        return (
          <div key={s} className="flex items-center gap-3">
            <div className="flex flex-col items-center">
              <div className={`grid place-items-center h-7 w-7 rounded-full border-2 transition-colors ${
                done ? 'border-primary bg-primary text-primary-foreground' : 'border-border bg-muted text-muted-foreground'
              }`}>
                {done ? <CheckCircle2 className="h-4 w-4" /> : <span className="text-xs">{i + 1}</span>}
              </div>
              {i < STATUS_STEPS.length - 1 && <div className={`w-0.5 h-6 ${i < idx ? 'bg-primary' : 'bg-border'}`} />}
            </div>
            <span className={`text-sm ${active ? 'font-semibold text-primary' : done ? 'text-foreground' : 'text-muted-foreground'}`}>{s}</span>
          </div>
        )
      })}
    </div>
  )
}

function TrackView({ initialCode }) {
  const [code, setCode] = useState(initialCode || '')
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(false)

  const search = useCallback(async (c) => {
    const q = (c ?? code).trim().toUpperCase()
    if (!q) return toast.error('Bitte gib deinen Auftragscode ein.')
    setLoading(true); setOrder(null)
    try {
      const res = await fetch(`/api/orders/track?code=${encodeURIComponent(q)}`)
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Nicht gefunden')
      setOrder(data)
    } catch (e) {
      toast.error(e.message || 'Auftrag nicht gefunden')
    } finally {
      setLoading(false)
    }
  }, [code])

  useEffect(() => { if (initialCode) search(initialCode) }, [initialCode]) // eslint-disable-line

  return (
    <div className="container py-10 max-w-2xl">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">Auftragsstatus prüfen</h1>
        <p className="text-muted-foreground">Gib deinen Auftragscode ein, um den aktuellen Stand zu sehen.</p>
      </div>
      <div className="flex gap-2 mb-8">
        <Input placeholder="z. B. AB12CD34" value={code} onChange={(e) => setCode(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === 'Enter' && search()} className="font-mono tracking-widest text-center text-lg" />
        <Button onClick={() => search()} disabled={loading} className="gap-2">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />} Suchen
        </Button>
      </div>

      <AnimatePresence>
        {order && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <Card className="glass-card">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>{order.model?.modelName || 'Druckauftrag'}</CardTitle>
                    <CardDescription className="font-mono">{order.orderNumber}</CardDescription>
                  </div>
                  <Badge className={STATUS_STYLES[order.status] || ''} variant="outline">{order.status}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {order.model?.image && (
                  <img src={order.model.image} alt="Modell" className="w-full h-48 object-cover rounded-lg border border-border" />
                )}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                  <Info label="Farbe" value={order.color} />
                  <Info label="Material" value={order.material} />
                  <Info label="Größe" value={`${order.size} %`} />
                  <Info label="Anzahl" value={order.quantity} />
                </div>

                <div>
                  <div className="text-sm font-medium mb-3">Fortschritt</div>
                  <StatusStepper status={order.status} />
                </div>

                {order.photos?.length > 0 && (
                  <div>
                    <div className="text-sm font-medium mb-2 flex items-center gap-2"><ImageIcon className="h-4 w-4" /> Fotos des Drucks</div>
                    <div className="grid grid-cols-3 gap-2">
                      {order.photos.map((p, i) => <img key={i} src={p} alt="Druck" className="aspect-square object-cover rounded-lg border border-border" />)}
                    </div>
                  </div>
                )}

                <div className="rounded-lg border border-primary/30 bg-primary/5 p-4 text-center">
                  <div className="text-xs text-muted-foreground">Geschätzter Preis</div>
                  <div className="text-2xl font-bold text-primary">ca. {eur(order.price?.total)}</div>
                  <div className="text-xs text-muted-foreground mt-1">Unverbindlich – wird nach Prüfung bestätigt.</div>
                </div>
                <a href={order.makerworldLink} target="_blank" rel="noreferrer" className="flex items-center justify-center gap-1.5 text-sm text-accent hover:underline">
                  <ExternalLink className="h-4 w-4" /> Modell auf MakerWorld ansehen
                </a>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function Info({ label, value }) {
  return (
    <div className="rounded-lg bg-muted/30 p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  )
}

// =============================================================
// Admin: Login + Dashboard
// =============================================================
function AdminView() {
  const [token, setToken] = useState(null)
  const [creds, setCreds] = useState({ username: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState([])
  const [editing, setEditing] = useState(null)

  useEffect(() => {
    const t = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null
    if (t) setToken(t)
  }, [])

  const login = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/admin/login', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(creds),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Login fehlgeschlagen')
      localStorage.setItem('admin_token', data.token)
      setToken(data.token)
      toast.success('Willkommen zurück!')
    } catch (e) {
      toast.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  const logout = () => { localStorage.removeItem('admin_token'); setToken(null); setOrders([]) }

  const loadOrders = useCallback(async () => {
    if (!token) return
    try {
      const res = await fetch('/api/orders', { headers: { Authorization: `Bearer ${token}` } })
      if (res.status === 401) { logout(); toast.error('Sitzung abgelaufen'); return }
      const data = await res.json()
      setOrders(data.orders || [])
    } catch (e) { toast.error('Aufträge konnten nicht geladen werden') }
  }, [token])

  useEffect(() => { loadOrders() }, [loadOrders])

  const updateOrder = async (id, patch) => {
    try {
      const res = await fetch(`/api/orders/${id}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(patch),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Fehler')
      setOrders((os) => os.map((o) => (o.id === id ? data.order : o)))
      if (editing?.id === id) setEditing(data.order)
      toast.success('Gespeichert')
      return data.order
    } catch (e) { toast.error(e.message) }
  }

  const deleteOrder = async (id) => {
    if (!confirm('Diesen Auftrag wirklich löschen?')) return
    try {
      const res = await fetch(`/api/orders/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } })
      if (!res.ok) throw new Error('Fehler')
      setOrders((os) => os.filter((o) => o.id !== id))
      toast.success('Auftrag gelöscht')
    } catch (e) { toast.error('Löschen fehlgeschlagen') }
  }

  const uploadPhotos = async (order, files) => {
    const readers = Array.from(files).map((f) => new Promise((resolve) => {
      const r = new FileReader(); r.onload = () => resolve(r.result); r.readAsDataURL(f)
    }))
    const base64s = await Promise.all(readers)
    await updateOrder(order.id, { photos: [...(order.photos || []), ...base64s] })
  }

  // ---- Login-Ansicht ----
  if (!token) {
    return (
      <div className="container py-16 max-w-sm">
        <Card className="glass-card">
          <CardHeader className="text-center">
            <div className="mx-auto mb-2 grid place-items-center h-12 w-12 rounded-xl bg-primary/15"><ShieldCheck className="h-6 w-6 text-primary" /></div>
            <CardTitle>Admin-Login</CardTitle>
            <CardDescription>Nur für den Betreiber</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2"><Label>Benutzername</Label>
              <Input value={creds.username} onChange={(e) => setCreds((c) => ({ ...c, username: e.target.value }))} onKeyDown={(e) => e.key === 'Enter' && login()} /></div>
            <div className="space-y-2"><Label>Passwort</Label>
              <Input type="password" value={creds.password} onChange={(e) => setCreds((c) => ({ ...c, password: e.target.value }))} onKeyDown={(e) => e.key === 'Enter' && login()} /></div>
            <Button className="w-full" onClick={login} disabled={loading}>{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Anmelden'}</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // ---- Dashboard ----
  const stats = STATUS_STEPS.map((s) => ({ s, n: orders.filter((o) => o.status === s).length }))
  return (
    <div className="container py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Auftragsverwaltung</h1>
          <p className="text-sm text-muted-foreground">{orders.length} Aufträge gesamt</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={loadOrders} className="gap-2"><RefreshCw className="h-4 w-4" /> Aktualisieren</Button>
          <Button variant="ghost" onClick={logout} className="gap-2"><LogOut className="h-4 w-4" /> Abmelden</Button>
        </div>
      </div>

      {/* Statistik */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 mb-6">
        {stats.map((st) => (
          <div key={st.s} className="rounded-lg border border-border bg-card/50 p-3 text-center">
            <div className="text-2xl font-bold">{st.n}</div>
            <div className="text-xs text-muted-foreground truncate">{st.s}</div>
          </div>
        ))}
      </div>

      {/* Auftragsliste */}
      {orders.length === 0 ? (
        <div className="text-center py-20 text-muted-foreground">
          <Boxes className="h-10 w-10 mx-auto mb-3 opacity-50" />
          Noch keine Aufträge vorhanden.
        </div>
      ) : (
        <div className="grid gap-4">
          {orders.map((o) => (
            <motion.div key={o.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <Card className="glass-card">
                <CardContent className="p-4">
                  <div className="flex flex-col lg:flex-row gap-4">
                    {/* Bild */}
                    <div className="h-24 w-24 shrink-0 rounded-lg overflow-hidden bg-muted grid place-items-center">
                      {o.model?.image ? <img src={o.model.image} alt="" className="h-full w-full object-cover" /> : <Printer className="h-8 w-8 text-muted-foreground" />}
                    </div>
                    {/* Infos */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold">{o.name}</span>
                        <Badge variant="outline" className="font-mono text-xs">{o.orderNumber}</Badge>
                        <Badge variant="outline" className="font-mono text-xs bg-primary/10 text-primary border-primary/30">Code: {o.customerCode}</Badge>
                        {o.priority === 'Eilig' && <Badge className="gap-1 bg-red-500/20 text-red-300 border-red-500/40" variant="outline"><Zap className="h-3 w-3" />Eilig</Badge>}
                      </div>
                      <div className="mt-1 text-sm text-muted-foreground truncate">{o.model?.modelName || o.makerworldLink}</div>
                      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                        <span>Farbe: <b>{o.color}</b></span>
                        <span>Material: <b>{o.material}</b></span>
                        <span>Größe: <b>{o.size}%</b></span>
                        <span>Anzahl: <b>{o.quantity}</b></span>
                        <span className="text-primary">Preis: <b>ca. {eur(o.price?.total)}</b></span>
                      </div>
                    </div>
                    {/* Aktionen */}
                    <div className="flex flex-row lg:flex-col gap-2 lg:w-52">
                      <Select value={o.status} onValueChange={(v) => updateOrder(o.id, { status: v })}>
                        <SelectTrigger className={`${STATUS_STYLES[o.status] || ''}`}><SelectValue /></SelectTrigger>
                        <SelectContent>{STATUS_STEPS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
                      </Select>
                      <div className="flex gap-2">
                        <Button size="sm" variant="secondary" className="flex-1 gap-1" onClick={() => setEditing(o)}><Pencil className="h-3.5 w-3.5" /> Details</Button>
                        <Button size="sm" variant="ghost" className="text-destructive" onClick={() => deleteOrder(o.id)}><Trash2 className="h-4 w-4" /></Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Detail-/Bearbeiten-Dialog */}
      <Dialog open={!!editing} onOpenChange={(v) => !v && setEditing(null)}>
        <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
          {editing && (
            <>
              <DialogHeader>
                <DialogTitle>{editing.name} · {editing.orderNumber}</DialogTitle>
                <DialogDescription>Auftragsdetails bearbeiten, Notizen &amp; Fotos verwalten</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1"><Label>Status</Label>
                    <Select value={editing.status} onValueChange={(v) => updateOrder(editing.id, { status: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>{STATUS_STEPS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1"><Label>Priorität</Label>
                    <Select value={editing.priority} onValueChange={(v) => updateOrder(editing.id, { priority: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>{PRIORITIES.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1"><Label>Größe</Label>
                    <Select value={String(editing.size)} onValueChange={(v) => updateOrder(editing.id, { size: parseInt(v) })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>{SIZES.map((s) => <SelectItem key={s} value={String(s)}>{s} %</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1"><Label>Anzahl</Label>
                    <Input type="number" min={1} defaultValue={editing.quantity} onBlur={(e) => updateOrder(editing.id, { quantity: Math.max(1, parseInt(e.target.value) || 1) })} />
                  </div>
                </div>

                <div className="rounded-lg bg-muted/30 p-3 text-sm space-y-1">
                  <div className="flex justify-between"><span className="text-muted-foreground">Kundencode</span><span className="font-mono text-primary">{editing.customerCode}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Geschätzter Preis</span><span className="font-semibold text-primary">ca. {eur(editing.price?.total)}</span></div>
                  <a href={editing.makerworldLink} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-accent hover:underline pt-1"><ExternalLink className="h-3.5 w-3.5" /> MakerWorld-Link</a>
                </div>

                <div className="space-y-1"><Label>Kunden-Notiz</Label><div className="rounded-md border border-border bg-muted/20 p-2 text-sm text-muted-foreground min-h-[40px]">{editing.notes || 'Keine Notiz'}</div></div>

                <div className="space-y-1"><Label>Interne Admin-Notiz</Label>
                  <Textarea defaultValue={editing.adminNotes} placeholder="Nur für dich sichtbar…" onBlur={(e) => updateOrder(editing.id, { adminNotes: e.target.value })} />
                </div>

                {/* Fotos */}
                <div className="space-y-2">
                  <Label className="flex items-center gap-2"><ImageIcon className="h-4 w-4" /> Fotos des fertigen Drucks</Label>
                  <div className="grid grid-cols-4 gap-2">
                    {(editing.photos || []).map((p, i) => (
                      <div key={i} className="relative group">
                        <img src={p} alt="" className="aspect-square object-cover rounded-lg border border-border" />
                        <button onClick={() => updateOrder(editing.id, { photos: editing.photos.filter((_, j) => j !== i) })}
                          className="absolute -top-1.5 -right-1.5 h-5 w-5 rounded-full bg-destructive grid place-items-center opacity-0 group-hover:opacity-100 transition">
                          <X className="h-3 w-3 text-white" />
                        </button>
                      </div>
                    ))}
                    <label className="aspect-square rounded-lg border-2 border-dashed border-border grid place-items-center cursor-pointer hover:border-primary/50 transition">
                      <Upload className="h-5 w-5 text-muted-foreground" />
                      <input type="file" accept="image/*" multiple className="hidden" onChange={(e) => e.target.files?.length && uploadPhotos(editing, e.target.files)} />
                    </label>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="secondary" onClick={() => setEditing(null)}>Schließen</Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

// =============================================================
// Root-App
// =============================================================
export default function App() {
  const [view, setView] = useState('home')
  const [lastOrder, setLastOrder] = useState(null)
  const [trackCode, setTrackCode] = useState('')

  return (
    <MotionConfig reducedMotion="never">
    <div className="min-h-screen app-bg text-foreground">
      <Header view={view} setView={setView} />
      <main>
        <AnimatePresence mode="wait">
          {view === 'home' && <motion.div key="home" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><HomeView setView={setView} setLastOrder={setLastOrder} /></motion.div>}
          {view === 'track' && <motion.div key="track" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><TrackView initialCode={trackCode} /></motion.div>}
          {view === 'admin' && <motion.div key="admin" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><AdminView /></motion.div>}
        </AnimatePresence>
      </main>

      <footer className="border-t border-border/60 py-8 mt-10">
        <div className="container text-center text-sm text-muted-foreground">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Printer className="h-4 w-4 text-primary" />
            <span className="font-semibold text-foreground">Janniks 3D-Druck Service</span>
          </div>
          Privates Auftragsportal · nur für Familie, Freunde &amp; Bekannte
        </div>
      </footer>

      <SuccessDialog
        order={lastOrder}
        onClose={() => setLastOrder(null)}
        goTrack={() => { setTrackCode(lastOrder.customerCode); setLastOrder(null); setView('track') }}
      />
      <Toaster position="top-center" richColors />
    </div>
    </MotionConfig>
  )
}
