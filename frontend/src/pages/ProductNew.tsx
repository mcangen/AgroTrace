import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../lib/api'
import { ErrorNote, Field, Spinner } from '../components/ui'
import { STATUS_LABELS } from '../lib/format'
import type { ProductInput, ProductStatus } from '../lib/types'

const STATUSES = Object.keys(STATUS_LABELS) as ProductStatus[]

export default function ProductNew() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: farms, isLoading: loadingFarms } = useQuery({
    queryKey: ['farms'],
    queryFn: api.listFarms,
  })

  const [form, setForm] = useState({
    farm_id: '',
    name: '',
    variety: '',
    status: 'GROWING' as ProductStatus,
    responsable: '',
    planting_date: '',
    harvest_date: '',
    insumos: '',
    post_cosecha: '',
    description: '',
  })

  const mutation = useMutation({
    mutationFn: (payload: ProductInput) => api.createProduct(payload),
    onSuccess: (product) => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      navigate(`/panel/lotes/${product.id}`)
    },
  })

  // Con una sola finca no tiene sentido pedir que la elija.
  const farmId = form.farm_id || (farms?.length === 1 ? String(farms[0].id) : '')

  function update(field: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!farmId) return
    mutation.mutate({
      farm_id: Number(farmId),
      name: form.name,
      variety: form.variety || null,
      status: form.status,
      responsable: form.responsable || null,
      planting_date: form.planting_date || null,
      harvest_date: form.harvest_date || null,
      insumos: form.insumos || null,
      post_cosecha: form.post_cosecha || null,
      description: form.description || null,
    })
  }

  if (loadingFarms) return <Spinner label="Cargando fincas…" />

  if (!farms || farms.length === 0) {
    return (
      <div className="card card-pad stack stack-4">
        <h1 className="display display-md">Primero registra una finca</h1>
        <p className="muted">Un lote siempre pertenece a una finca.</p>
        <Link to="/panel/fincas" className="btn btn-primary" style={{ alignSelf: 'start' }}>
          Ir a fincas
        </Link>
      </div>
    )
  }

  return (
    <div className="stack stack-5" style={{ maxWidth: 760 }}>
      <header>
        <Link to="/panel/lotes" className="small muted">
          ← Lotes
        </Link>
        <h1 className="display display-lg" style={{ marginTop: 'var(--sp-2)' }}>
          Registrar un lote
        </h1>
        <p className="lede" style={{ marginTop: 'var(--sp-2)' }}>
          Al guardar se crea el primer eslabón de la cadena: un evento de registro inicial
          sellado con SHA-256.
        </p>
      </header>

      <form className="card card-pad stack stack-5" onSubmit={handleSubmit}>
        {mutation.error != null && <ErrorNote error={mutation.error} />}

        <div className="form-grid">
          <Field label="Finca">
            <select
              className="select"
              value={farmId}
              onChange={(e) => update('farm_id', e.target.value)}
              required
            >
              <option value="">Selecciona una finca…</option>
              {farms.map((farm) => (
                <option key={farm.id} value={farm.id}>
                  {farm.name}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Estado actual">
            <select
              className="select"
              value={form.status}
              onChange={(e) => update('status', e.target.value)}
            >
              {STATUSES.map((value) => (
                <option key={value} value={value}>
                  {STATUS_LABELS[value]}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Nombre del producto">
            <input
              className="input"
              value={form.name}
              onChange={(e) => update('name', e.target.value)}
              placeholder="Cacao fino de aroma"
              required
              minLength={2}
            />
          </Field>

          <Field label="Variedad">
            <input
              className="input"
              value={form.variety}
              onChange={(e) => update('variety', e.target.value)}
              placeholder="CCN-51"
            />
          </Field>

          <Field label="Responsable">
            <input
              className="input"
              value={form.responsable}
              onChange={(e) => update('responsable', e.target.value)}
              placeholder="Familia Pérez"
            />
          </Field>

          <Field label="Fecha de siembra">
            <input
              className="input"
              type="date"
              value={form.planting_date}
              onChange={(e) => update('planting_date', e.target.value)}
            />
          </Field>

          <Field label="Fecha de cosecha">
            <input
              className="input"
              type="date"
              value={form.harvest_date}
              onChange={(e) => update('harvest_date', e.target.value)}
            />
          </Field>
        </div>

        <Field
          label="Insumos empleados"
          hint="Los agentes de IA solo pueden mencionar lo que quede registrado aquí."
        >
          <textarea
            className="textarea"
            value={form.insumos}
            onChange={(e) => update('insumos', e.target.value)}
            placeholder="Compost propio, ceniza de cascarilla, sin agroquímicos de síntesis"
          />
        </Field>

        <Field label="Manejo post-cosecha">
          <textarea
            className="textarea"
            value={form.post_cosecha}
            onChange={(e) => update('post_cosecha', e.target.value)}
            placeholder="Fermentación en cajones de madera 6 días, secado solar en marquesina"
          />
        </Field>

        <Field label="Descripción">
          <textarea
            className="textarea"
            value={form.description}
            onChange={(e) => update('description', e.target.value)}
            placeholder="Cultivado a 600 msnm bajo sombra de árboles nativos."
          />
        </Field>

        <div className="row" style={{ gap: 'var(--sp-3)' }}>
          <button className="btn btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? <span className="spin" /> : 'Registrar y sellar'}
          </button>
          <Link to="/panel/lotes" className="btn btn-ghost">
            Cancelar
          </Link>
        </div>
      </form>
    </div>
  )
}
