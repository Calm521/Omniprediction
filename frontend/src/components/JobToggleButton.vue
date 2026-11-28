<template>
  <button
    v-if="visible"
    class="job-toggle"
    :class="[state, { busy }]"
    :disabled="busy"
    :title="tooltip"
    @click="onClick"
  >
    <span class="job-toggle-icon" aria-hidden="true">
      <svg v-if="state === 'paused'" viewBox="0 0 24 24" width="12" height="12" fill="currentColor">
        <path d="M8 5v14l11-7z" />
      </svg>
      <svg v-else-if="busy" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.4">
        <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round" />
      </svg>
      <svg v-else viewBox="0 0 24 24" width="12" height="12" fill="currentColor">
        <rect x="6" y="5" width="4" height="14" rx="1" />
        <rect x="14" y="5" width="4" height="14" rx="1" />
      </svg>
    </span>
    <span class="job-toggle-label">{{ label }}</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  // 'running' | 'paused' | 'idle'
  state: { type: String, default: 'idle' },
  busy: { type: Boolean, default: false },
  visible: { type: Boolean, default: true },
})

const emit = defineEmits(['pause', 'resume'])
const { t } = useI18n()

const label = computed(() => {
  if (props.state === 'paused') return t('common.resume')
  return t('common.pause')
})

const tooltip = computed(() => {
  if (props.state === 'paused') return t('common.resumeHint')
  return t('common.pauseHint')
})

const onClick = () => {
  if (props.busy) return
  if (props.state === 'paused') emit('resume')
  else emit('pause')
}
</script>

<style scoped>
.job-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 12px;
  border: 1px solid #E0E0E0;
  border-radius: 6px;
  background: #FFF;
  color: #333;
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
  white-space: nowrap;
}

.job-toggle:hover:not(:disabled) {
  background: #111;
  border-color: #111;
  color: #FFF;
}

.job-toggle.paused {
  border-color: #111;
  color: #111;
}

.job-toggle.paused:hover:not(:disabled) {
  background: #111;
  color: #FFF;
}

.job-toggle:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.job-toggle-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.job-toggle.busy .job-toggle-icon svg {
  animation: job-toggle-spin 0.9s linear infinite;
}

@keyframes job-toggle-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.job-toggle-label {
  line-height: 1;
}
</style>
