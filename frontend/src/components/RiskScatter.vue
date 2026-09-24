<script setup>
import { ref, watch, onMounted } from 'vue'
import * as d3 from 'd3'

const props = defineProps({ patients: Array, selected: Object, whatIf: Object, xFeature: Object, tiers: Object })
const emit = defineEmits(['pick'])
const el = ref(null)
const W = 680, H = 380, M = { t: 14, r: 16, b: 44, l: 48 }
const col = (t) => getComputedStyle(document.documentElement).getPropertyValue(`--${t}`).trim()

function draw() {
  const f = props.xFeature, { low, high } = props.tiers
  const ymax = Math.max(0.6, Math.ceil(d3.max(props.patients, (p) => p.risk) * 10) / 10)
  const jit = f.max - f.min <= 30 ? f.step * 0.7 : 0
  const x = d3.scaleLinear().domain([f.min, f.max]).range([M.l, W - M.r])
  const y = d3.scaleLinear().domain([0, ymax]).range([H - M.b, M.t])
  const svg = d3.select(el.value).attr('viewBox', `0 0 ${W} ${H}`)
  svg.selectAll('*').remove()

  ;[['low', 0, low], ['moderate', low, high], ['high', high, ymax]].forEach(([t, a, b]) =>
    svg.append('rect').attr('x', M.l).attr('width', W - M.l - M.r).attr('y', y(b)).attr('height', y(a) - y(b)).attr('fill', col(t)).attr('opacity', 0.08))
  svg.append('g').attr('transform', `translate(0,${H - M.b})`).call(d3.axisBottom(x).ticks(8))
  svg.append('g').attr('transform', `translate(${M.l},0)`).call(d3.axisLeft(y).ticks(6).tickFormat(d3.format('.0%')))
  svg.append('text').attr('x', (M.l + W - M.r) / 2).attr('y', H - 8).attr('text-anchor', 'middle').attr('font-size', 13)
    .attr('fill', '#5b6b78').text(`${f.label}${f.unit ? ' (' + f.unit + ')' : ''}`)
  svg.append('text').attr('transform', 'rotate(-90)').attr('x', -(H - M.b + M.t) / 2).attr('y', 13).attr('text-anchor', 'middle')
    .attr('font-size', 13).attr('fill', '#5b6b78').text('30-day readmission probability')

  const px = (p, i) => x(p.features[f.key] + ((((i * 9301 + 49297) % 233280) / 233280) - 0.5) * jit)
  svg.selectAll('circle.pt').data(props.patients).join('circle').attr('class', 'pt')
    .attr('cx', px).attr('cy', (p) => y(p.risk)).attr('r', 4.5)
    .attr('fill', (p) => col(p.tier)).attr('opacity', 0.7).style('cursor', 'pointer')
    .on('click', (_, p) => emit('pick', p))
    .append('title').text((p) => `${p.id}: ${Math.round(p.risk * 100)}%`)

  const s = props.selected
  if (!s) return
  const i = props.patients.indexOf(s)
  const sx = px(s, i), sy = y(s.risk)
  svg.append('circle').attr('cx', sx).attr('cy', sy).attr('r', 9).attr('fill', 'none').attr('stroke', '#14222e').attr('stroke-width', 2)
  const w = props.whatIf
  if (w) {
    const wx = x(Math.min(Math.max(w.x, f.min), f.max)), wy = y(Math.min(w.y, ymax))
    svg.append('line').attr('x1', sx).attr('y1', sy).attr('x2', wx).attr('y2', wy).attr('stroke', '#14222e').attr('stroke-dasharray', '4 3')
    svg.append('circle').attr('cx', wx).attr('cy', wy).attr('r', 8).attr('fill', col(w.tier)).attr('stroke', '#fff').attr('stroke-width', 2.5)
  }
}
onMounted(draw)
watch(() => [props.patients, props.selected, props.whatIf, props.xFeature], draw)
</script>

<template><svg ref="el" width="100%" role="img" aria-label="Cohort scatter of readmission risk with selected patient and what-if position" /></template>
