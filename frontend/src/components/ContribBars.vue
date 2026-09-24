<script setup>
import { ref, watch, onMounted } from 'vue'
import * as d3 from 'd3'

const props = defineProps({ items: Array })
const el = ref(null)
const W = 460, ROW = 30, LAB = 170

function draw() {
  const data = [...props.items].sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
  const m = Math.max(0.08, d3.max(data, (d) => Math.abs(d.value)) * 1.1)
  const x = d3.scaleLinear().domain([-m, m]).range([LAB + 50, W - 56])
  const svg = d3.select(el.value).attr('viewBox', `0 0 ${W} ${data.length * ROW + 8}`)
  const t = d3.transition().duration(160)

  svg.selectAll('line.axis').data([0]).join('line').attr('class', 'axis')
    .attr('x1', x(0)).attr('x2', x(0)).attr('y1', 0).attr('y2', data.length * ROW + 8)
    .attr('stroke', '#9aa9b5')

  const rows = svg.selectAll('g.row').data(data, (d) => d.key).join((enter) => {
    const g = enter.append('g').attr('class', 'row').attr('transform', (d, i) => `translate(0,${i * ROW})`)
    g.append('text').attr('class', 'lab').attr('x', 0).attr('y', ROW / 2 + 4).attr('font-size', 13).text((d) => d.label)
    g.append('rect').attr('y', 5).attr('height', ROW - 10).attr('rx', 2)
    g.append('text').attr('class', 'val').attr('y', ROW / 2 + 4).attr('font-size', 12).attr('font-weight', 600)
    return g
  })
  rows.transition(t).attr('transform', (d, i) => `translate(0,${i * ROW})`)
  rows.select('rect').transition(t)
    .attr('x', (d) => Math.min(x(0), x(d.value))).attr('width', (d) => Math.abs(x(d.value) - x(0)))
    .attr('fill', (d) => (d.value >= 0 ? 'var(--high)' : 'var(--low)'))
  rows.select('.val').text((d) => `${d.value >= 0 ? '+' : '−'}${Math.abs(d.value * 100).toFixed(1)}`)
    .transition(t)
    .attr('x', (d) => (d.value >= 0 ? x(d.value) + 6 : x(d.value) - 6))
    .attr('text-anchor', (d) => (d.value >= 0 ? 'start' : 'end'))
}
onMounted(draw)
watch(() => props.items, draw)
</script>

<template><svg ref="el" class="bars" width="100%" role="img" aria-label="Contribution of each risk factor, in percentage points" /></template>
