<script setup lang="ts">
import { ref } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import ItineraryForm from '@/components/ItineraryForm.vue'
import ItineraryResult from '@/components/ItineraryResult.vue'
import {
  generateItinerary,
  GENERATION_FAILED_MESSAGE,
  type Itinerary,
  type ItineraryRequest,
} from '@/api/itinerary'

// 화면 상태 머신 (PRD §4 흐름)
type Status = 'input' | 'loading' | 'error' | 'result'
const status = ref<Status>('input')
const itinerary = ref<Itinerary>()
const errorMsg = ref('')
let lastPayload: ItineraryRequest | null = null

async function run(payload: ItineraryRequest) {
  lastPayload = payload
  status.value = 'loading'
  try {
    itinerary.value = await generateItinerary(payload)
    status.value = 'result'
  } catch (e) {
    errorMsg.value = e instanceof Error && e.message ? e.message : GENERATION_FAILED_MESSAGE
    status.value = 'error'
  }
}

const onSubmit = (p: ItineraryRequest) => run(p)
const retryOrRegenerate = () => lastPayload && run(lastPayload)
const reset = () => (status.value = 'input')
</script>

<template>
  <div class="planner-page">
    <!-- S1 IntroHeader (제목 + 서브텍스트 위계) -->
    <div v-if="status === 'input'" class="intro">
      <h1 class="intro-title">AI 여행 일정 생성기</h1>
      <p class="intro-subtitle">여행지와 조건을 입력하면 AI가 일자별 여행 일정을 만들어드려요.</p>
    </div>

    <!-- S2 InputForm -->
    <ItineraryForm v-if="status === 'input'" @submit="onSubmit" />

    <!-- S5 LoadingState -->
    <div v-else-if="status === 'loading'" class="state">
      <el-icon class="spin" :size="44"><Loading /></el-icon>
      <p>AI가 일정을 만들고 있어요…</p>
    </div>

    <!-- S6 ErrorState -->
    <el-result v-else-if="status === 'error'" icon="error" :sub-title="errorMsg">
      <template #extra>
        <el-button type="primary" @click="retryOrRegenerate">다시 시도</el-button>
        <el-button @click="reset">조건 새로 입력</el-button>
      </template>
    </el-result>

    <!-- S7 ResultView -->
    <ItineraryResult
      v-else-if="itinerary"
      :itinerary="itinerary"
      @regenerate="retryOrRegenerate"
      @reset="reset"
    />
  </div>
</template>

<style scoped>
.planner-page {
  max-width: 720px;
  margin: 0 auto;
  padding: 1rem 0.5rem 3rem;
}
.intro {
  text-align: center;
  margin-bottom: 2rem;
}
.intro-title {
  margin: 0 0 0.5rem;
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.intro-subtitle {
  margin: 0;
  font-size: 0.95rem;
  color: var(--el-text-color-secondary);
}
.state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 4rem 0;
  color: var(--el-text-color-secondary);
}
.spin {
  color: var(--el-color-primary);
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
