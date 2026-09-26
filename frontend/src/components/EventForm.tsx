/** Formulario para sellar un evento nuevo en la cadena de un lote.
 *
 * El payload es un conjunto de pares dato/valor libres, porque cada cultivo
 * mide cosas distintas. Se sugieren campos según la etapa para que el registro
 * sea consistente sin volverse rígido.
 */

import { useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { api } from '../lib/api'
import { EVENT_LABELS, EVENT_ORDER } from '../lib/format'
import { ErrorNote, Field } from './ui'
import type { EventPhoto, EventType } from '../lib/types'

const SUGGESTED_FIELDS: Partial<Record<EventType, string[]>> = {
  SIEMBRA: ['area_m2', 'variedad', 'plantulas'],
  LABOR_CULTURAL: ['labor', 'jornales'],
  FERTILIZACION: ['insumo', 'dosis_kg_ha', 'metodo'],
  CONTROL_FITOSANITARIO: ['objetivo', 'metodo', 'quimicos'],
  COSECHA: ['kg', 'calidad', 'cosechado_por'],
  POST_COSECHA: ['proceso', 'dias', 'recipiente'],
  SECADO: ['metodo', 'dias', 'humedad_final_pct'],
  CONTROL_CALIDAD: ['humedad_pct', 'granos_defectuosos_pct', 'observacion'],
  EMPAQUE: ['sacos', 'kg_por_saco', 'empaque', 'lote'],
  CERTIFICACION: ['certificacion', 'entidad', 'vigencia'],
  DESPACHO: ['destino', 'transportador', 'guia'],
}

type Pair = { key: string; value: string }

function pairsFor(eventType: EventType): Pair[] {
  const fields = SUGGESTED_FIELDS[eventType] ?? ['detalle']
  return fields.map((key) => ({ key, value: '' }))
}

export default function EventForm({
  productId,
  onDone,
}: {
  productId: number
  onDone: () => void
}) {
  const queryClient = useQueryClient()
  const [eventType, setEventType] = useState<EventType>('COSECHA')
  const [pairs, setPairs] = useState<Pair[]>(() => pairsFor('COSECHA'))
  const [note, setNote] = useState('')
  const [occurredAt, setOccurredAt] = useState('')
  const [photos, setPhotos] = useState<EventPhoto[]>([])
  const [photoError, setPhotoError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Las fotos se suben antes de sellar el evento: su huella tiene que existir
  // para poder entrar al payload que se firma.
  const upload = useMutation({
    mutationFn: (file: File) => api.uploadPhoto(productId, file),
    onSuccess: (photo) => setPhotos((prev) => [...prev, photo]),
    onError: (error: unknown) =>
      setPhotoError(error instanceof Error ? error.message : 'No se pudo subir la foto.'),
  })

  const mutation = useMutation({
    mutationFn: () => {
      const payload: Record<string, string> = {}
      for (const pair of pairs) {
        const key = pair.key.trim()
        if (key && pair.value.trim()) payload[key] = pair.value.trim()
      }
      return api.createEvent(productId, {
        event_type: eventType,
        payload,
        note: note.trim() || null,
        // El input date no lleva hora; se sella al mediodía para evitar que la
        // zona horaria mueva el evento al día anterior.
        occurred_at: occurredAt ? new Date(`${occurredAt}T12:00:00`).toISOString() : null,
        photo_ids: photos.map((p) => p.id),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events', productId] })
      queryClient.invalidateQueries({ queryKey: ['verify', productId] })
      queryClient.invalidateQueries({ queryKey: ['product', productId] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['products'] })
      onDone()
    },
  })

  function changeType(next: EventType) {
    setEventType(next)
    setPairs(pairsFor(next))
  }

  function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    setPhotoError(null)
    const files = Array.from(event.target.files ?? [])
    // Se suben una por una para poder reportar cuál falló, si alguna falla.
    files.forEach((file) => upload.mutate(file))
    event.target.value = '' // permite volver a elegir el mismo archivo
  }

  function removePhoto(photo: EventPhoto) {
    // Aún no está sellada en ningún evento, así que se puede descartar del todo.
    api.deletePhoto(productId, photo.id).catch(() => {
      /* si el borrado en servidor falla, igual se quita de este formulario */
    })
    setPhotos((prev) => prev.filter((p) => p.id !== photo.id))
  }

  function updatePair(index: number, part: Partial<Pair>) {
    setPairs((prev) => prev.map((pair, i) => (i === index ? { ...pair, ...part } : pair)))
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    mutation.mutate()
  }

  return (
    <form className="card card-pad stack stack-4" onSubmit={handleSubmit}>
      <h3 className="display display-sm">Sellar un evento nuevo</h3>

      {mutation.error != null && <ErrorNote error={mutation.error} />}

      <div className="form-grid">
        <Field label="Etapa">
          <select
            className="select"
            value={eventType}
            onChange={(e) => changeType(e.target.value as EventType)}
          >
            {EVENT_ORDER.map((type) => (
              <option key={type} value={type}>
                {EVENT_LABELS[type]}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Fecha del hecho" hint="Si la dejas vacía se usa la fecha de hoy.">
          <input
            className="input"
            type="date"
            value={occurredAt}
            onChange={(e) => setOccurredAt(e.target.value)}
          />
        </Field>
      </div>

      <div className="stack stack-2">
        <span className="field-label">Datos del evento</span>
        {pairs.map((pair, index) => (
          <div className="row" key={index} style={{ gap: 'var(--sp-2)' }}>
            <input
              className="input"
              style={{ flex: '0 0 40%' }}
              value={pair.key}
              onChange={(e) => updatePair(index, { key: e.target.value })}
              placeholder="dato"
              aria-label={`Nombre del dato ${index + 1}`}
            />
            <input
              className="input"
              value={pair.value}
              onChange={(e) => updatePair(index, { value: e.target.value })}
              placeholder="valor"
              aria-label={`Valor del dato ${index + 1}`}
            />
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => setPairs((prev) => prev.filter((_, i) => i !== index))}
              aria-label={`Quitar dato ${index + 1}`}
            >
              ✕
            </button>
          </div>
        ))}
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          style={{ alignSelf: 'flex-start' }}
          onClick={() => setPairs((prev) => [...prev, { key: '', value: '' }])}
        >
          + Agregar dato
        </button>
      </div>

      <Field label="Nota (opcional)">
        <textarea
          className="textarea"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Observaciones del operario en campo…"
        />
      </Field>

      <div className="stack stack-2">
        <span className="field-label">Fotos de evidencia (opcional)</span>
        <span className="field-hint">
          La huella de cada foto se sella dentro del evento, así que después nadie puede
          sustituirla sin que se note. JPG, PNG o WEBP, hasta 8 MB.
        </span>

        {photos.length > 0 && (
          <div className="photo-grid">
            {photos.map((photo) => (
              <figure className="photo-thumb" key={photo.id}>
                <img src={photo.url} alt={photo.caption ?? photo.filename} loading="lazy" />
                <button
                  type="button"
                  className="photo-remove"
                  onClick={() => removePhoto(photo)}
                  aria-label={`Quitar ${photo.filename}`}
                  title="Quitar foto"
                >
                  ✕
                </button>
              </figure>
            ))}
          </div>
        )}

        {photoError && <ErrorNote error={new Error(photoError)} />}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          style={{ display: 'none' }}
          onChange={handleFiles}
        />
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          style={{ alignSelf: 'flex-start' }}
          onClick={() => fileInputRef.current?.click()}
          disabled={upload.isPending}
        >
          {upload.isPending ? <span className="spin" /> : '📷 Agregar foto'}
        </button>
      </div>

      <div className="row" style={{ gap: 'var(--sp-3)' }}>
        <button className="btn btn-primary" disabled={mutation.isPending || upload.isPending}>
          {mutation.isPending ? <span className="spin" /> : 'Sellar evento'}
        </button>
        <button type="button" className="btn btn-ghost" onClick={onDone}>
          Cancelar
        </button>
      </div>
    </form>
  )
}
