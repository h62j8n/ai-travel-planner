<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import type { Category, Itinerary } from '@/api/itinerary'

defineProps<{ itinerary: Itinerary }>()
defineEmits<{ (e: 'regenerate'): void; (e: 'reset'): void }>()

// §6.4 8개 카테고리 아이콘 매핑
const CATEGORY_ICON: Record<Category, string> = {
  '체험&액티비티': '🎯',
  자연: '🌿',
  '유명 관광지': '📸',
  힐링: '🌸',
  '문화&예술&역사': '🏛️',
  쇼핑: '🛍️',
  먹방: '🍜',
  'SNS 핫플레이스': '✨',
}

function formatCost(cost?: number): string {
  if (!cost) return '무료'
  return `${cost.toLocaleString('ko-KR')}원`
}
function formatDuration(min: number): string {
  const h = Math.floor(min / 60)
  const m = min % 60
  return h ? `${h}시간${m ? ` ${m}분` : ''}` : `${m}분`
}
</script>

<template>
  <div class="result">
    <!-- S7-1 ResultSummary -->
    <el-card class="summary" shadow="never">
      <h2 class="summary-dest">
        {{ itinerary.destination }}
        <span class="summary-days">{{ itinerary.duration_days }}일</span>
      </h2>
      <p class="summary-line">{{ itinerary.summary }}</p>
    </el-card>

    <!-- S7-2 DayTimeline -->
    <div v-for="d in itinerary.days" :key="d.day" class="day-card">
      <div class="day-head">
        <el-tag type="primary" effect="dark" round>Day {{ d.day }}</el-tag>
        <span class="day-theme">{{ d.theme }}</span>
      </div>

      <el-timeline>
        <el-timeline-item
          v-for="a in d.activities"
          :key="a.id"
          :timestamp="a.time"
          placement="top"
          type="primary"
          hollow
        >
          <div class="activity">
            <div class="activity-top">
              <strong class="activity-title">
                {{ CATEGORY_ICON[a.category] }} {{ a.title }}
              </strong>
              <el-tag size="small" effect="plain">{{ a.category }}</el-tag>
            </div>
            <p class="activity-desc">{{ a.description }}</p>
            <p class="activity-meta">
              📍 {{ a.location }} · ⏱ {{ formatDuration(a.duration_minutes) }} · 💰
              {{ formatCost(a.estimated_cost) }}
            </p>
            <p v-if="a.tips" class="activity-tip">💡 {{ a.tips }}</p>
          </div>
        </el-timeline-item>
      </el-timeline>
    </div>

    <!-- S7-3 RegenerateAction -->
    <div class="actions">
      <el-button :icon="Refresh" @click="$emit('regenerate')">같은 조건으로 다시 생성</el-button>
      <el-button text @click="$emit('reset')">조건 새로 입력</el-button>
    </div>
  </div>
</template>

<style scoped>
.result {
  max-width: 640px;
  margin: 0 auto;
}
.summary {
  margin-bottom: 1.5rem;
  border: none;
  background: var(--el-color-primary-light-9);
}
.summary-dest {
  margin: 0 0 0.4rem;
  font-size: 1.4rem;
}
.summary-days {
  margin-left: 0.5rem;
  font-size: 1rem;
  color: var(--el-color-primary);
  font-weight: 600;
}
.summary-line {
  margin: 0;
  color: var(--el-text-color-regular);
}
.day-card {
  margin-bottom: 1.5rem;
}
.day-head {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1rem;
}
.day-theme {
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.activity-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
}
.activity-title {
  font-size: 1rem;
}
.activity-desc {
  margin: 0.35rem 0;
  color: var(--el-text-color-regular);
  font-size: 0.9rem;
}
.activity-meta {
  margin: 0;
  font-size: 0.82rem;
  color: var(--el-text-color-secondary);
}
.activity-tip {
  margin: 0.35rem 0 0;
  font-size: 0.82rem;
  color: var(--el-color-warning);
}
.actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  margin-top: 2rem;
}
</style>
