<template>
  <div class="project-start">
    <header class="app-header">
      <span class="brand">Omniprediction</span>
      <LanguageSwitcher />
    </header>

    <main class="content">
      <section class="create-project">
        <p class="eyebrow">{{ $t('home.realitySeed') }}</p>
        <h1>{{ $t('home.startEngine') }}</h1>

        <div
          class="upload-zone"
          :class="{ dragging: isDragOver }"
          @click="fileInput?.click()"
          @dragover.prevent="isDragOver = true"
          @dragleave.prevent="isDragOver = false"
          @drop.prevent="handleDrop"
        >
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".pdf,.md,.markdown,.txt"
            @change="addFiles($event.target.files)"
          />
          <strong>{{ $t('home.dragToUpload') }}</strong>
          <span>{{ $t('home.supportedFormats') }}</span>
        </div>

        <ul v-if="files.length" class="file-list">
          <li v-for="(file, index) in files" :key="`${file.name}-${index}`">
            <span>{{ file.name }}</span>
            <button type="button" :aria-label="`Remove ${file.name}`" @click="files.splice(index, 1)">×</button>
          </li>
        </ul>

        <label class="field-label" for="simulation-requirement">{{ $t('home.simulationPrompt') }}</label>
        <textarea
          id="simulation-requirement"
          v-model="simulationRequirement"
          :placeholder="$t('home.promptPlaceholder')"
          rows="5"
        />

        <button class="start-button" type="button" :disabled="!canSubmit" @click="startProject">
          {{ $t('home.startEngine') }} <span aria-hidden="true">→</span>
        </button>
      </section>

      <HistoryDatabase />
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import HistoryDatabase from '../components/HistoryDatabase.vue'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import { setPendingUpload } from '../store/pendingUpload'

const router = useRouter()
const fileInput = ref(null)
const files = ref([])
const simulationRequirement = ref('')
const isDragOver = ref(false)
const canSubmit = computed(() => files.value.length > 0 && simulationRequirement.value.trim().length > 0)

function addFiles(selectedFiles) {
  const validFiles = Array.from(selectedFiles || []).filter(file =>
    ['pdf', 'md', 'markdown', 'txt'].includes(file.name.split('.').pop()?.toLowerCase())
  )
  files.value.push(...validFiles)
  if (fileInput.value) fileInput.value.value = ''
}

function handleDrop(event) {
  isDragOver.value = false
  addFiles(event.dataTransfer.files)
}

function startProject() {
  if (!canSubmit.value) return
  setPendingUpload(files.value, simulationRequirement.value.trim())
  router.push({ name: 'Process', params: { projectId: 'new' } })
}
</script>

<style scoped>
.project-start { min-height: 100vh; background: #fff; color: #111; }
.app-header { min-height: 72px; padding: 18px clamp(24px, 4vw, 64px); border-bottom: 1px solid #e8e8e8; display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.brand { font-family: 'JetBrains Mono', monospace; font-size: clamp(20px, 2vw, 28px); font-weight: 800; letter-spacing: -.04em; overflow-wrap: anywhere; }
.content { max-width: 1180px; margin: 0 auto; padding: 48px 24px 80px; }
.create-project { max-width: 760px; margin: 0 auto 72px; }
.eyebrow { font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #555; }
h1 { margin: 12px 0 32px; font-size: clamp(28px, 4vw, 42px); }
.upload-zone { min-height: 152px; padding: 30px; border: 2px dashed #bbb; border-radius: 12px; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 10px; text-align: center; cursor: pointer; }
.upload-zone:hover, .upload-zone.dragging { border-color: #111; background: #f8f8f8; }
.upload-zone input { display: none; }
.upload-zone span { color: #666; font-size: 14px; }
.file-list { list-style: none; margin: 14px 0 26px; padding: 0; }
.file-list li { display: flex; justify-content: space-between; gap: 16px; padding: 10px 0; border-bottom: 1px solid #eee; overflow-wrap: anywhere; }
.file-list button { flex: none; border: 0; background: none; font-size: 24px; cursor: pointer; }
.field-label { display: block; margin: 28px 0 10px; font-weight: 700; }
textarea { display: block; width: 100%; padding: 16px; border: 1px solid #bbb; border-radius: 10px; resize: vertical; font: inherit; }
.start-button { margin-top: 20px; padding: 14px 24px; border: 0; border-radius: 8px; background: #111; color: #fff; font: inherit; font-weight: 700; cursor: pointer; }
.start-button:disabled { background: #aaa; cursor: not-allowed; }
.start-button span { margin-left: 18px; }
</style>
