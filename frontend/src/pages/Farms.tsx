import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../lib/api'
import ConfirmDialog from '../components/ConfirmDialog'
import WeatherPanel from '../components/WeatherPanel'
import { EmptyState, ErrorNote, Field, Spinner } from '../components/ui'
import { formatNumber } from '../lib/format'
import type { Farm, FarmInput } from '../lib/types'

const EMPTY: FarmInput = {
  name: '',
  owner_name: '',
  municipality: '',
  department: '',
  country: 'Colombia',
  altitude_m: null,
  area_ha: null,
  description: '',
}

export default function Farms() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<FarmInput>(EMPTY)
  const [farmToDelete, setFarmToDelete] = useState<Farm | null>(null)
  const [weatherOpened, setWeatherOpened] = useState<Set<number>>(() => new Set())

  const farms = useQuery({ queryKey: ['farms'], queryFn: api.listFarms })

  const create = useMutation({
    mutationFn: (payload: FarmInput) => api.createFarm(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['farms'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setForm(EMPTY)
      setShowForm(false)
    },
  })

  // Eliminar una finca elimina en cascada sus lotes, eventos y pasaportes
  // (lo hace la base de datos), asi que hay que refrescar todo lo que dependa.
  const remove = useMutation({
    mutationFn: (id: number) => api.deleteFarm(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['farms'] })
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setFarmToDelete(null)
    },
  })

  function update<K extends keyof FarmInput>(field: K, value: FarmInput[K]) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    create.mutate({
      ...form,
      owner_name: form.owner_name || null,
      municipality: form.municipality || null,
      department: form.department || null,
      description: form.description || null,
    })
  }

  if (farms.isLoading) return <Spinner label="Cargando fincas…" />
  if (farms.error) return <ErrorNote error={farms.error} />

  return (
    <div className="stack stack-5">
      <header className="page-head">
        <div>
          <span className="eyebrow">Tu operación</span>
          <h1 className="display display-lg" style={{ marginTop: 'var(--sp-2)' }}>
            Fincas
          </h1>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? 'Cerrar' : '+ Nueva finca'}
        </button>
      </header>

      {showForm && (
        <form className="card card-pad stack stack-4" onSubmit={handleSubmit}>
          {create.error != null && <ErrorNote error={create.error} />}

          <div className="form-grid">
            <Field label="Nombre de la finca">
              <input
                className="input"
                value={form.name}
                onChange={(e) => update('name', e.target.value)}
                required
                minLength={2}
                placeholder="Finca La Esperanza"
              />
            </Field>
            <Field label="Productor responsable">
              <input
                className="input"
                value={form.owner_name ?? ''}
                onChange={(e) => update('owner_name', e.target.value)}
                placeholder="Familia Pérez"
              />
            </Field>
            <Field label="Municipio">
              <input
                className="input"
                value={form.municipality ?? ''}
                onChange={(e) => update('municipality', e.target.value)}
                placeholder="Ciénaga"
              />
            </Field>
            <Field label="Departamento">
              <input
                className="input"
                value={form.department ?? ''}
                onChange={(e) => update('department', e.target.value)}
                placeholder="Magdalena"
              />
            </Field>
            <Field label="Altitud (msnm)">
              <input
                className="input"
                type="number"
                min={0}
                max={6000}
                value={form.altitude_m ?? ''}
                onChange={(e) =>
                  update('altitude_m', e.target.value ? Number(e.target.value) : null)
                }
                placeholder="600"
              />
            </Field>
            <Field label="Área (hectáreas)">
              <input
                className="input"
                type="number"
                min={0}
                step="0.1"
                value={form.area_ha ?? ''}
                onChange={(e) =>
                  update('area_ha', e.target.value ? Number(e.target.value) : null)
                }
                placeholder="12.5"
              />
            </Field>
          </div>

          <Field label="Descripción">
            <textarea
              className="textarea"
              value={form.description ?? ''}
              onChange={(e) => update('description', e.target.value)}
              placeholder="Finca familiar en la vertiente norte de la Sierra Nevada…"
            />
          </Field>

          <div className="row" style={{ gap: 'var(--sp-3)' }}>
            <button className="btn btn-primary" disabled={create.isPending}>
              {create.isPending ? <span className="spin" /> : 'Crear finca'}
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setShowForm(false)}
            >
              Cancelar
            </button>
          </div>
        </form>
      )}

      {!farms.data || farms.data.length === 0 ? (
        <EmptyState
          icon="⌂"
          title="No tienes fincas registradas"
          body="Crea tu primera finca para poder registrar lotes trazables."
          action={
            <button className="btn btn-primary" onClick={() => setShowForm(true)}>
              Crear finca
            </button>
          }
        />
      ) : (
        <div className="product-grid">
          {farms.data.map((farm) => (
            <article className="product-card" key={farm.id}>
              <div className="row row-between" style={{ alignItems: 'flex-start' }}>
                <h2 className="product-card-name">{farm.name}</h2>
                <button
                  type="button"
                  className="icon-btn icon-btn-danger"
                  onClick={() => setFarmToDelete(farm)}
                  aria-label={`Eliminar ${farm.name}`}
                  title="Eliminar finca"
                >
                  🗑
                </button>
              </div>
              <p className="small muted">{farm.location}</p>
              {farm.description && <p className="small">{farm.description}</p>}
              <div className="product-card-stats">
                <div>
                  <div className="product-stat-value">
                    {formatNumber(farm.product_count)}
                  </div>
                  <div className="product-stat-label">lotes</div>
                </div>
                {farm.altitude_m != null && (
                  <div>
                    <div className="product-stat-value">
                      {formatNumber(farm.altitude_m)}
                    </div>
                    <div className="product-stat-label">msnm</div>
                  </div>
                )}
                {farm.area_ha != null && (
                  <div>
                    <div className="product-stat-value">{formatNumber(farm.area_ha, 1)}</div>
                    <div className="product-stat-label">hectáreas</div>
                  </div>
                )}
              </div>

              {/* El pronóstico se pide solo cuando el productor despliega la
                  sección, y una vez abierta se deja montada para no repetir
                  la llamada al abrir y cerrar. */}
              <details
                onToggle={(event) => {
                  if (event.currentTarget.open) {
                    setWeatherOpened((prev) => new Set(prev).add(farm.id))
                  }
                }}
              >
                <summary className="small" style={{ cursor: 'pointer', fontWeight: 600 }}>
                  🌦 Clima y alertas
                </summary>
                <div style={{ marginTop: 'var(--sp-3)' }}>
                  {weatherOpened.has(farm.id) && <WeatherPanel farmId={farm.id} />}
                </div>
              </details>
            </article>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={farmToDelete != null}
        title={`¿Eliminar ${farmToDelete?.name ?? 'esta finca'}?`}
        body={
          farmToDelete && farmToDelete.product_count > 0 ? (
            <>
              Esta finca tiene <strong>{formatNumber(farmToDelete.product_count)}</strong>{' '}
              {farmToDelete.product_count === 1 ? 'lote registrado' : 'lotes registrados'}.
              Al eliminarla también se eliminarán esos lotes, todos sus eventos sellados y
              sus pasaportes públicos. Esta acción no se puede deshacer.
            </>
          ) : (
            'Esta acción no se puede deshacer.'
          )
        }
        busy={remove.isPending}
        error={remove.error}
        onCancel={() => {
          setFarmToDelete(null)
          remove.reset()
        }}
        onConfirm={() => farmToDelete && remove.mutate(farmToDelete.id)}
      />
    </div>
  )
}
