<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import RiskScatter from './components/RiskScatter.vue'
import ContribBars from './components/ContribBars.vue'
import RiskGauge from './components/RiskGauge.vue'

const meta = ref(null)
const cohort = ref([])
const selId = ref(null)
const values = reactive({})
const result = ref(null)
const xKey = ref('age')
const filter = ref('all')
const error = ref('')
let timer, seq = 0

const sel = computed(() => cohort.value.find((p) => p.id === selId.value))
const label = (k) => meta.value.features.find((f) => f.key === k).label
const xFeature = computed(() => meta.value.features.find((f) => f.key === xKey.value))
const dirty = computed(() => sel.value && meta.value.features.some((f) => values[f.key] !== sel.value.features[f.key]))
const delta = computed(() => (result.value && sel.value ? (result.value.risk - sel.value.risk) * 100 : 0))
const queue = computed(() => cohort.value.filter((p) => filter.value === 'all' || p.tier === filter.value))
const items = computed(() => result.value.contributions.map((c) => ({ ...c, label: label(c.key) })))
const whatIf = computed(() => (dirty.value ? { x: values[xKey.value], y: result.value.risk, tier: result.value.tier } : null))
const counts = computed(() => Object.fromEntries(['high', 'moderate', 'low'].map((t) => [t, cohort.value.filter((p) => p.tier === t).length])))

function select(p) {
  selId.value = p.id
  Object.assign(values, p.features)
  result.value = { risk: p.risk, tier: p.tier, contributions: p.contributions }
}
function onSlide() {
  clearTimeout(timer)
  timer = setTimeout(async () => {
    const mine = ++seq
    try {
      const r = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ features: { ...values } }),
      })
      if (!r.ok) throw new Error(await r.text())
      const data = await r.json()
      if (mine === seq) result.value = data
    } catch (e) {
      error.value = 'Could not reach the prediction service. Start the API on port 8000.'
    }
  }, 90)
}
const fmt = (f, v) => (f.step < 1 ? Number(v).toFixed(1) : v)

onMounted(async () => {
  try {
    meta.value = await (await fetch('/api/meta')).json()
    cohort.value = await (await fetch('/api/cohort')).json()
    select(cohort.value[0])
  } catch (e) {
    error.value = 'Could not reach the prediction service. Start the API on port 8000.'
  }
})
</script>

<template>
  <div v-if="error" class="fail">{{ error }}</div>
  <div v-else-if="!meta || !result" class="fail">Loading model and cohort…</div>
  <div v-else class="shell">
    <header>
      <div>
        <h1>30-day readmission risk</h1>
        <p>Synthetic cohort of {{ cohort.length }} discharges. Gradient-boosted model, held-out AUC {{ meta.auc }}, base rate {{ Math.round(meta.prevalence * 100) }}%.</p>
      </div>
      <div class="tally">
        <span v-for="t in ['high', 'moderate', 'low']" :key="t"><i :class="t" />{{ counts[t] }} {{ t }}</span>
      </div>
    </header>

    <aside class="queue">
      <h2>Triage queue</h2>
      <div class="chips" role="group" aria-label="Filter by tier">
        <button v-for="t in ['all', 'high', 'moderate', 'low']" :key="t" :class="{ on: filter === t }" @click="filter = t">{{ t }}</button>
      </div>
      <ul>
        <li v-for="p in queue" :key="p.id">
          <button :class="{ on: p.id === selId }" @click="select(p)">
            <i :class="p.tier" />
            <span class="id">{{ p.id }}</span>
            <span class="drv">{{ label(p.top_driver) }}</span>
            <b>{{ Math.round(p.risk * 100) }}%</b>
          </button>
        </li>
      </ul>
    </aside>

    <main>
      <section class="card">
        <div class="row">
          <h2>Where this patient sits in the cohort</h2>
          <label>Plot against
            <select v-model="xKey"><option v-for="f in meta.features" :key="f.key" :value="f.key">{{ f.label }}</option></select>
          </label>
        </div>
        <RiskScatter :patients="cohort" :selected="sel" :what-if="whatIf" :x-feature="xFeature" :tiers="meta.tiers" @pick="select" />
      </section>
      <section class="card">
        <h2>What is driving the risk</h2>
        <p class="hint">Change in probability versus a patient with cohort-average values for that factor.</p>
        <ContribBars :items="items" />
      </section>
    </main>

    <aside class="panel">
      <section class="card">
        <div class="row">
          <h2>{{ sel.id }}</h2>
          <button class="reset" :disabled="!dirty" @click="select(sel)">Reset to chart values</button>
        </div>
        <RiskGauge :risk="result.risk" :tier="result.tier" :tiers="meta.tiers" />
        <p class="delta" :class="{ up: delta > 0.05, down: delta < -0.05 }">
          <template v-if="!dirty">Recorded risk at discharge</template>
          <template v-else>{{ delta >= 0 ? '+' : '−' }}{{ Math.abs(delta).toFixed(1) }} points from recorded {{ Math.round(sel.risk * 100) }}%</template>
        </p>
      </section>
      <section class="card">
        <h2>Adjust risk factors</h2>
        <div v-for="f in meta.features" :key="f.key" class="slider">
          <label :for="f.key">
            <span>{{ f.label }}<em v-if="values[f.key] !== sel.features[f.key]"> (edited)</em></span>
            <b>{{ fmt(f, values[f.key]) }} {{ f.unit }}</b>
          </label>
          <input :id="f.key" type="range" v-model.number="values[f.key]" :min="f.min" :max="f.max" :step="f.step" :class="result.tier" @input="onSlide" />
        </div>
      </section>
    </aside>
    <footer>Demonstration on synthetic data. Not validated for clinical decisions.</footer>
  </div>
</template>

<style>
:root {
  --paper: #f2f5f7; --panel: #fff; --ink: #14222e; --muted: #5b6b78; --line: #d8e0e6; --accent: #1f5f8b;
  --low: #2e8b6a; --moderate: #d9992b; --high: #c8473f;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink); font: 15px/1.45 'Public Sans', system-ui, sans-serif; }
h1 { font-size: 26px; margin: 0 0 2px; letter-spacing: -0.01em; }
h2 { font-size: 16px; margin: 0 0 10px; }
p { margin: 0; color: var(--muted); }
button, select { font: inherit; color: inherit; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.fail { padding: 60px 24px; text-align: center; color: var(--muted); }
.shell { display: grid; grid-template-columns: 290px minmax(0, 1fr) 340px; gap: 16px; padding: 20px; max-width: 1500px; margin: 0 auto; }
header { grid-column: 1 / -1; display: flex; justify-content: space-between; align-items: end; flex-wrap: wrap; gap: 8px; }
footer { grid-column: 1 / -1; font-size: 13px; color: var(--muted); }
.tally { display: flex; gap: 16px; font-weight: 500; }
i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
i.low { background: var(--low); } i.moderate { background: var(--moderate); } i.high { background: var(--high); }
.card, .queue { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }
main, .panel { display: flex; flex-direction: column; gap: 16px; min-width: 0; }
.row { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }
.row label { font-size: 13px; color: var(--muted); }
select { border: 1px solid var(--line); border-radius: 6px; padding: 4px 6px; background: #fff; margin-left: 4px; }
.hint { font-size: 13px; margin: -6px 0 6px; }
.queue { align-self: start; position: sticky; top: 12px; }
.chips { display: flex; gap: 6px; margin-bottom: 10px; }
.chips button { border: 1px solid var(--line); background: #fff; border-radius: 999px; padding: 2px 10px; font-size: 13px; cursor: pointer; text-transform: capitalize; }
.chips button.on { background: var(--ink); color: #fff; border-color: var(--ink); }
.queue ul { list-style: none; margin: 0; padding: 0; max-height: calc(100vh - 170px); overflow-y: auto; }
.queue li button { width: 100%; display: grid; grid-template-columns: 16px 58px 1fr auto; align-items: center; text-align: left; padding: 7px 8px; border: 0; border-bottom: 1px solid var(--line); background: none; cursor: pointer; }
.queue li button:hover { background: var(--paper); }
.queue li button.on { background: #e4eef5; }
.drv { font-size: 12px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0 8px; }
.reset { border: 1px solid var(--line); background: #fff; border-radius: 6px; padding: 3px 10px; font-size: 13px; cursor: pointer; }
.reset:disabled { opacity: 0.4; cursor: default; }
.delta { text-align: center; font-weight: 500; }
.delta.up { color: var(--high); } .delta.down { color: var(--low); }
.slider { margin-bottom: 12px; }
.slider label { display: flex; justify-content: space-between; font-size: 14px; }
.slider em { color: var(--accent); font-style: normal; font-size: 12px; }
input[type='range'] { width: 100%; margin: 4px 0 0; accent-color: var(--accent); }
input.low { accent-color: var(--low); } input.moderate { accent-color: var(--moderate); } input.high { accent-color: var(--high); }
@media (max-width: 1100px) { .shell { grid-template-columns: 1fr; } .queue { position: static; } .queue ul { max-height: 260px; } }
</style>
