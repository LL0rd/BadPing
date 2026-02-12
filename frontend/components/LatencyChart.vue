<script setup lang="ts">
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, ScatterChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  MarkAreaComponent,
  LegendComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, LineChart, ScatterChart, GridComponent, TooltipComponent, DataZoomComponent, MarkAreaComponent, LegendComponent])

const props = defineProps<{
  points: { timestamp: number; latency_ms: number | null; packet_lost: boolean; ping_type?: string | null }[]
  pingType?: string
}>()

const colorMode = useColorMode()

const legendSelected = ref<Record<string, boolean>>({})

function onLegendSelectChanged(params: any) {
  legendSelected.value = { ...params.selected }
}

const option = computed(() => {
  const isDark = colorMode.value === 'dark'
  const textColor = isDark ? '#94a3b8' : '#64748b'
  const gridColor = isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(0, 0, 0, 0.06)'
  const icmpColor = '#22c55e'
  const arpColor = '#3b82f6'

  const isDualMode = props.pingType === 'both'

  if (isDualMode) {
    const icmpLatency = props.points
      .filter(p => p.ping_type === 'icmp' && !p.packet_lost && p.latency_ms !== null)
      .map(p => [p.timestamp * 1000, p.latency_ms])

    const arpLatency = props.points
      .filter(p => p.ping_type === 'arp' && !p.packet_lost && p.latency_ms !== null)
      .map(p => [p.timestamp * 1000, p.latency_ms])

    const lossData = props.points
      .filter(p => p.packet_lost)
      .map(p => [p.timestamp * 1000, 0])

    return {
      backgroundColor: 'transparent',
      grid: {
        top: 40,
        right: 20,
        bottom: 60,
        left: 60,
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: isDark ? '#1e293b' : '#fff',
        borderColor: isDark ? '#334155' : '#e2e8f0',
        textStyle: { color: isDark ? '#e2e8f0' : '#1e293b', fontSize: 12 },
        formatter(params: any) {
          if (!Array.isArray(params)) params = [params]
          const date = new Date(params[0].value[0]).toLocaleString()
          let html = `<div style="font-size:11px;color:${textColor}">${date}</div>`
          for (const p of params) {
            if (p.seriesName === 'ICMP Latency') {
              html += `<div style="margin-top:4px"><span style="color:${icmpColor}">&#9679;</span> ICMP: ${p.value[1].toFixed(2)}ms</div>`
            } else if (p.seriesName === 'ARP Latency') {
              html += `<div style="margin-top:4px"><span style="color:${arpColor}">&#9679;</span> ARP: ${p.value[1].toFixed(2)}ms</div>`
            } else if (p.seriesName === 'Packet Loss') {
              html += `<div style="margin-top:4px"><span style="color:#ef4444">&#9679;</span> Packet Lost</div>`
            }
          }
          return html
        },
      },
      legend: {
        show: true,
        top: 8,
        right: 10,
        textStyle: { color: textColor, fontSize: 11 },
        itemWidth: 12,
        itemHeight: 8,
        ...(Object.keys(legendSelected.value).length > 0 ? { selected: legendSelected.value } : {}),
      },
      xAxis: {
        type: 'time',
        axisLabel: { color: textColor, fontSize: 11 },
        axisLine: { lineStyle: { color: gridColor } },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        name: 'Latency (ms)',
        nameTextStyle: { color: textColor, fontSize: 11 },
        axisLabel: { color: textColor, fontSize: 11 },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: gridColor } },
      },
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100,
        },
        {
          type: 'slider',
          start: 0,
          end: 100,
          height: 24,
          bottom: 10,
          borderColor: gridColor,
          fillerColor: isDark ? 'rgba(34, 197, 94, 0.1)' : 'rgba(34, 197, 94, 0.15)',
          handleStyle: { color: icmpColor },
          textStyle: { color: textColor, fontSize: 10 },
        },
      ],
      series: [
        {
          name: 'ICMP Latency',
          type: 'line',
          data: icmpLatency,
          smooth: true,
          symbol: 'none',
          lineStyle: { color: icmpColor, width: 1.5 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: isDark ? 'rgba(34, 197, 94, 0.15)' : 'rgba(34, 197, 94, 0.2)' },
                { offset: 1, color: 'rgba(34, 197, 94, 0)' },
              ],
            },
          },
        },
        {
          name: 'ARP Latency',
          type: 'line',
          data: arpLatency,
          smooth: true,
          symbol: 'none',
          lineStyle: { color: arpColor, width: 1.5 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: isDark ? 'rgba(59, 130, 246, 0.15)' : 'rgba(59, 130, 246, 0.2)' },
                { offset: 1, color: 'rgba(59, 130, 246, 0)' },
              ],
            },
          },
        },
        {
          name: 'Packet Loss',
          type: 'scatter',
          data: lossData,
          symbol: 'triangle',
          symbolSize: 10,
          itemStyle: { color: '#ef4444' },
        },
      ],
    }
  }

  // Single mode (original behavior)
  const lineColor = icmpColor

  const latencyData = props.points
    .filter(p => !p.packet_lost && p.latency_ms !== null)
    .map(p => [p.timestamp * 1000, p.latency_ms])

  const lossData = props.points
    .filter(p => p.packet_lost)
    .map(p => [p.timestamp * 1000, 0])

  return {
    backgroundColor: 'transparent',
    grid: {
      top: 40,
      right: 20,
      bottom: 60,
      left: 60,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? '#1e293b' : '#fff',
      borderColor: isDark ? '#334155' : '#e2e8f0',
      textStyle: { color: isDark ? '#e2e8f0' : '#1e293b', fontSize: 12 },
      formatter(params: any) {
        if (!Array.isArray(params)) params = [params]
        const date = new Date(params[0].value[0]).toLocaleString()
        let html = `<div style="font-size:11px;color:${textColor}">${date}</div>`
        for (const p of params) {
          if (p.seriesName === 'Latency') {
            html += `<div style="margin-top:4px"><span style="color:${lineColor}">&#9679;</span> ${p.value[1].toFixed(2)}ms</div>`
          } else if (p.seriesName === 'Packet Loss') {
            html += `<div style="margin-top:4px"><span style="color:#ef4444">&#9679;</span> Packet Lost</div>`
          }
        }
        return html
      },
    },
    legend: {
      show: true,
      top: 8,
      right: 10,
      textStyle: { color: textColor, fontSize: 11 },
      itemWidth: 12,
      itemHeight: 8,
      ...(Object.keys(legendSelected.value).length > 0 ? { selected: legendSelected.value } : {}),
    },
    xAxis: {
      type: 'time',
      axisLabel: { color: textColor, fontSize: 11 },
      axisLine: { lineStyle: { color: gridColor } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: 'Latency (ms)',
      nameTextStyle: { color: textColor, fontSize: 11 },
      axisLabel: { color: textColor, fontSize: 11 },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: gridColor } },
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        height: 24,
        bottom: 10,
        borderColor: gridColor,
        fillerColor: isDark ? 'rgba(34, 197, 94, 0.1)' : 'rgba(34, 197, 94, 0.15)',
        handleStyle: { color: lineColor },
        textStyle: { color: textColor, fontSize: 10 },
      },
    ],
    series: [
      {
        name: 'Latency',
        type: 'line',
        data: latencyData,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: lineColor, width: 1.5 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: isDark ? 'rgba(34, 197, 94, 0.15)' : 'rgba(34, 197, 94, 0.2)' },
              { offset: 1, color: 'rgba(34, 197, 94, 0)' },
            ],
          },
        },
      },
      {
        name: 'Packet Loss',
        type: 'scatter',
        data: lossData,
        symbol: 'triangle',
        symbolSize: 10,
        itemStyle: { color: '#ef4444' },
      },
    ],
  }
})
</script>

<template>
  <div class="rounded-xl border border-border bg-card p-4">
    <VChart
      v-if="points.length > 0"
      :option="option"
      :update-options="{ notMerge: false }"
      autoresize
      style="height: 350px; width: 100%"
      @legendselectchanged="onLegendSelectChanged"
    />
    <div v-else class="flex h-[350px] items-center justify-center text-sm text-muted-foreground">
      No data available for the selected time range
    </div>
  </div>
</template>
