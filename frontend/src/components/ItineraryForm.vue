<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { Swiper, SwiperSlide } from 'swiper/vue'
import type { Swiper as SwiperType } from 'swiper'
import 'swiper/css'
import { ArrowUp, ArrowDown } from '@element-plus/icons-vue'
import { CATEGORIES, COMPANIONS, type ItineraryRequest } from '@/api/itinerary'

const emit = defineEmits<{ (e: 'submit', payload: ItineraryRequest): void }>()

// 목적지 — 국내 한정(§2). 권역 → 세부 지역 2단 연동.
const REGIONS: { group: string; items: string[] }[] = [
  { group: '수도권', items: ['서울', '인천', '수원', '가평', '양평', '파주', '강화'] },
  { group: '강원도', items: ['강릉', '속초', '양양', '춘천', '평창', '정선', '삼척'] },
  { group: '충청도', items: ['대전', '세종', '단양', '제천', '태안', '보령', '공주'] },
  { group: '전라도', items: ['전주', '군산', '여수', '순천', '담양', '목포', '남원'] },
  { group: '경상도', items: ['부산', '대구', '울산', '경주', '안동', '포항', '통영', '거제', '남해'] },
  { group: '제주도', items: ['제주', '서귀포'] },
]

// 스텝 순서 (질문 = 한 슬라이드)
type QKey = 'destination' | 'dateRange' | 'activityTime' | 'companion' | 'preferences' | 'budget'
const QUESTIONS: { key: QKey; title: string }[] = [
  { key: 'destination', title: '여행지를 선택하세요' },
  { key: 'dateRange', title: '여행 기간을 선택하세요' },
  { key: 'activityTime', title: '활동 시간을 선택하세요' },
  { key: 'companion', title: '누구와 함께 가나요?' },
  { key: 'preferences', title: '어떤 취향의 여행인가요?' },
  { key: 'budget', title: '예산 수준을 알려주세요' },
]

const form = reactive({
  region: '',
  destination: '',
  dateRange: null as [string, string] | null,
  timeRange: null as [string, string] | null,
  companion: '',
  preferences: [] as string[],
  budget: '',
})

const regionItems = computed(() => REGIONS.find((g) => g.group === form.region)?.items ?? [])
function onRegionChange() {
  form.destination = ''
}

function togglePref(c: string) {
  const i = form.preferences.indexOf(c)
  if (i >= 0) form.preferences.splice(i, 1)
  else form.preferences.push(c)
}

// 현재 질문 필수 검증 → 통과 시 '' , 실패 시 경고 문구 (§5.3)
function validateStep(i: number): string {
  switch (QUESTIONS[i].key) {
    case 'destination':
      return form.destination ? '' : '여행지를 선택해주세요.'
    case 'dateRange': {
      if (!form.dateRange) return '여행 기간을 선택해주세요.'
      const [s, e] = form.dateRange
      const days = Math.floor((new Date(e).getTime() - new Date(s).getTime()) / 86_400_000) + 1
      if (days > 30) return '여행 기간은 최대 30일까지 가능해요.'
      return ''
    }
    case 'activityTime':
      return form.timeRange ? '' : '활동 시간을 선택해주세요.'
    case 'companion':
      return form.companion ? '' : '동반인을 선택해주세요.'
    case 'preferences':
      return form.preferences.length ? '' : '취향을 하나 이상 선택해주세요.'
    case 'budget': {
      const b = form.budget.trim()
      if (!b) return '예산 수준을 입력해주세요.'
      if (b.length > 30) return '예산 수준은 최대 30자까지 입력할 수 있어요.'
      return ''
    }
  }
}

const swiper = ref<SwiperType>()
const step = ref(0)
const warning = ref('')
const isLast = computed(() => step.value === QUESTIONS.length - 1)
// 프로그래스바 진행률 (현재 스텝 기준)
const progress = computed(() => Math.round(((step.value + 1) / QUESTIONS.length) * 100))
// 모든 질문이 채워졌는지 — '일정 생성하기' 버튼 노출 조건
const allComplete = computed(() => QUESTIONS.every((_, i) => validateStep(i) === ''))
let reverting = false

const onSwiper = (sw: SwiperType) => (swiper.value = sw)

// 앞으로 이동일 때만 게이팅: 직전 질문 미입력이면 되돌리고 경고 노출.
function onSlideChange(sw: SwiperType) {
  if (reverting) {
    reverting = false
    return
  }
  const from = step.value
  const to = sw.activeIndex
  if (to > from) {
    const msg = validateStep(from)
    if (msg) {
      warning.value = msg
      reverting = true
      sw.slideTo(from)
      return
    }
  }
  step.value = to
  warning.value = ''
}

const goPrev = () => swiper.value?.slidePrev()
const goNext = () => swiper.value?.slideNext()

// 마지막 스텝 CTA (구 S4 GenerateAction). 전 스텝 재검증 후 payload emit.
function submit() {
  for (let i = 0; i < QUESTIONS.length; i++) {
    const msg = validateStep(i)
    if (msg) {
      warning.value = msg
      swiper.value?.slideTo(i)
      return
    }
  }
  emit('submit', {
    destination: form.destination,
    start_date: form.dateRange![0],
    end_date: form.dateRange![1],
    activity_time_start: form.timeRange![0],
    activity_time_end: form.timeRange![1],
    companion: form.companion as ItineraryRequest['companion'],
    preferences: [...form.preferences],
    budget_level: form.budget.trim(),
  })
}
</script>

<template>
  <section class="stepper" tabindex="0" @keydown.up.prevent="goPrev" @keydown.down.prevent="goNext">
    <!-- 프로그래스바 -->
    <el-progress class="progress" :percentage="progress" :show-text="false" :stroke-width="6" />

    <!-- 캐러셀 + 오버레이 꺽쇠 (이전/다음 질문이 위아래로 흐리게 peek) -->
    <div class="carousel">
      <Swiper
      class="q-swiper"
      direction="vertical"
      :slides-per-view="2.4"
      :centered-slides="true"
      :space-between="16"
      :grab-cursor="true"
      :no-swiping-selector="'.el-select, .el-date-editor, .el-input, .el-radio-group, .el-checkbox-group, .el-button, input'"
      @swiper="onSwiper"
      @slide-change="onSlideChange"
    >
      <SwiperSlide v-for="q in QUESTIONS" :key="q.key" class="q-slide">
        <div class="panel">
          <h2 class="q-title">{{ q.title }}</h2>

          <!-- S2-1 DestinationField -->
          <template v-if="q.key === 'destination'">
            <div class="row">
              <el-select v-model="form.region" placeholder="권역 선택" @change="onRegionChange">
                <el-option v-for="g in REGIONS" :key="g.group" :label="g.group" :value="g.group" />
              </el-select>
              <el-select v-model="form.destination" placeholder="세부 지역" :disabled="!form.region">
                <el-option v-for="r in regionItems" :key="r" :label="r" :value="r" />
              </el-select>
            </div>
          </template>

          <!-- S2-2 DateRangeField -->
          <template v-else-if="q.key === 'dateRange'">
            <el-date-picker
              v-model="form.dateRange"
              type="daterange"
              value-format="YYYY-MM-DD"
              range-separator="~"
              start-placeholder="시작일"
              end-placeholder="종료일"
            />
            <p class="q-hint">최대 30일까지 선택할 수 있어요.</p>
          </template>

          <!-- S2-3 ActivityTimeField -->
          <template v-else-if="q.key === 'activityTime'">
            <el-time-picker
              v-model="form.timeRange"
              is-range
              format="HH:mm"
              value-format="HH:mm"
              range-separator="~"
              start-placeholder="시작 시간"
              end-placeholder="종료 시간"
            />
          </template>

          <!-- S2-4 CompanionField -->
          <template v-else-if="q.key === 'companion'">
            <el-radio-group v-model="form.companion">
              <el-radio-button v-for="c in COMPANIONS" :key="c" :value="c">{{ c }}</el-radio-button>
            </el-radio-group>
          </template>

          <!-- S2-5 PreferenceField -->
          <template v-else-if="q.key === 'preferences'">
            <div class="chips">
              <el-check-tag
                v-for="cat in CATEGORIES"
                :key="cat"
                :checked="form.preferences.includes(cat)"
                @change="togglePref(cat)"
              >
                {{ cat }}
              </el-check-tag>
            </div>
          </template>

          <!-- S2-6 BudgetField -->
          <template v-else>
            <el-input
              v-model="form.budget"
              maxlength="30"
              show-word-limit
              placeholder="예: 1인당 15만원 이내 / 가성비 위주 / 여유롭게"
            />
          </template>
        </div>
      </SwiperSlide>
    </Swiper>

      <!-- 오버레이 꺽쇠: 현재 질문 위(이전)·아래(다음) 사이에 위치 -->
      <el-button class="chevron chevron--up" :class="{ hidden: step === 0 }" text @click="goPrev">
        <el-icon :size="22"><ArrowUp /></el-icon>
      </el-button>
      <el-button class="chevron chevron--down" :class="{ hidden: isLast }" text @click="goNext">
        <el-icon :size="22"><ArrowDown /></el-icon>
      </el-button>
    </div>

    <!-- 인라인 경고 (구 S3 ValidationNotice 흡수) -->
    <p class="q-warn" :class="{ show: warning }">{{ warning || ' ' }}</p>

    <!-- 모든 값 입력 완료 시 생성 CTA (꺽쇠와 분리된 하단 위치) -->
    <el-button v-if="allComplete" class="submit" type="primary" size="large" round @click="submit">
      일정 생성하기
    </el-button>
  </section>
</template>

<style scoped>
.stepper {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 440px;
  width: 100%;
  margin: 0 auto;
  outline: none;
}
.progress {
  width: 100%;
  margin-bottom: 0.75rem;
}

/* 캐러셀 + 오버레이 꺽쇠 */
.carousel {
  position: relative;
  width: 100%;
}
.chevron {
  position: absolute;
  left: 50%;
  z-index: 5;
  height: 34px;
  color: var(--el-color-primary);
  /* Element Plus가 인접 버튼에 주는 margin-left 제거 (중앙 정렬 어긋남 방지) */
  margin-left: 0 !important;
}
/* hover/focus/active 시에도 배경 없이 꺽쇠만 */
.chevron:hover,
.chevron:focus,
.chevron:active {
  background-color: transparent !important;
  color: var(--el-color-primary-light-3);
}
/* 현재 질문과 이전/다음 질문 사이(슬라이드 경계)에 배치 */
.chevron--up {
  top: 29%;
  transform: translate(-50%, -50%);
}
.chevron--down {
  top: 71%;
  transform: translate(-50%, -50%);
}
/* 첫/마지막 슬라이드에서 꺽쇠 숨김 (공간은 유지) */
.chevron.hidden {
  visibility: hidden;
}

/* Swiper */
.q-swiper {
  width: 100%;
  height: 52vh;
  min-height: 380px;
  max-height: 480px;
}
.q-slide {
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  padding: 0 0.5rem;
  opacity: 0.45;
  transform: scale(0.86);
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.q-swiper :deep(.swiper-slide-active) {
  opacity: 1;
  transform: scale(1);
}
.q-swiper :deep(.swiper-slide-prev) {
  opacity: 0.6;
}
.q-swiper :deep(.swiper-slide-next) {
  opacity: 0.45;
}
.panel {
  width: 100%;
  text-align: center;
}
.q-title {
  margin: 0 0 1.25rem;
  font-size: 1.35rem;
}
.q-hint {
  margin: 0.6rem 0 0;
  font-size: 0.8rem;
  color: var(--el-text-color-secondary);
}
.q-warn {
  min-height: 1.2rem;
  margin: 0.5rem 0 0.25rem;
  font-size: 0.85rem;
  color: var(--el-color-danger);
  opacity: 0;
  transition: opacity 0.15s;
}
.q-warn.show {
  opacity: 1;
}
.submit {
  margin-top: 0.25rem;
  min-width: 180px;
}

/* 슬라이드 내부 컨트롤 */
.row {
  display: flex;
  gap: 0.6rem;
  justify-content: center;
}
.row .el-select {
  flex: 1;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
}
</style>
