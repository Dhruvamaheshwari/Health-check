<script setup>
import { computed } from 'vue'
import * as d3 from 'd3'

const props = defineProps({ risk: Number, tier: String, tiers: Object })
const MAX = 0.8
const ang = (v) => -Math.PI / 2 + (Math.min(v, MAX) / MAX) * Math.PI
const arc = (a, b, r0, r1) => d3.arc()({ innerRadius: r0, outerRadius: r1, startAngle: ang(a), endAngle: ang(b) })
const bands = computed(() => [
  { d: arc(0, props.tiers.low, 78, 100), c: 'var(--low)' },
  { d: arc(props.tiers.low, props.tiers.high, 78, 100), c: 'var(--moderate)' },
  { d: arc(props.tiers.high, MAX, 78, 100), c: 'var(--high)' },
])
const fill = computed(() => arc(0, props.risk, 78, 100))
</script>

<template>
  <svg viewBox="-120 -115 240 135" role="img" :aria-label="`Readmission risk ${Math.round(risk * 100)} percent, ${tier} tier`">
    <path v-for="b in bands" :key="b.c" :d="b.d" :fill="b.c" opacity="0.22" />
    <path :d="fill" :fill="`var(--${tier})`" />
    <text y="-10" text-anchor="middle" font-size="40" font-weight="700" fill="currentColor">{{ Math.round(risk * 100) }}%</text>
    <text y="12" text-anchor="middle" font-size="14" fill="currentColor" style="text-transform: capitalize">{{ tier }} risk</text>
  </svg>
</template>
