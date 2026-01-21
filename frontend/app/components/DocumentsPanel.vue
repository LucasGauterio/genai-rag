<script setup lang="ts">
import type { Document } from '~/composables/useAppState'
import { FLASHCARD_COUNT_MAX, FLASHCARD_COUNT_MIN } from '~/composables/useAppState'

const {
  documents,
  addDocument,
  removeDocument,
  ingestDocument,
  hasIngestedDocuments,
  isGeneratingFlashcards,
  flashcardCount,
  flashcards,
  openFlashcardPanel,
  generateFlashcards,
  sessionId,
  sessionLoadState
} = useAppState()

const sessionFlashcards = ref<Record<string, any[]>>({})
const fileInput = ref<HTMLInputElement | null>(null)

const hasFlashcards = computed(() => {
  if (!sessionId.value) return false
  return (sessionFlashcards.value[sessionId.value] || []).length > 0
})

const currentFlashcardCount = computed(() => {
  return sessionId.value ? (sessionFlashcards.value[sessionId.value]?.length || 0) : 0
})

interface SessionResponse {
  session_id: string
  created_at: string
  chunk_count: number
  documents: Array<{
    document_id: string
    filename: string
    chunks: number
  }>
}

watch(() => sessionId.value, async (newSessionId, oldSessionId) => {
  if (oldSessionId) {
    sessionFlashcards.value[oldSessionId] = [...flashcards.value]
  }

  flashcards.value = []

  if (!newSessionId) {
    documents.value = []
    sessionFlashcards.value = {}
    return
  }

  try {
    if (sessionFlashcards.value[newSessionId]) {
      flashcards.value = [...sessionFlashcards.value[newSessionId]]
    }
    sessionLoadState.value = 'loading'
    const response = await $fetch<SessionResponse>(`/api/sessions/${newSessionId}`)

    documents.value = response.documents.map(doc => ({
      file: new File([], doc.filename),
      status: 'ingested' as const,
      chunksIngested: doc.chunks
    }))
    sessionLoadState.value = 'idle'
  } catch (err) {
    console.error('Failed to fetch session documents:', err)
    sessionLoadState.value = 'error'
  }
})

watch(flashcards, (newFlashcards) => {
  if (sessionId.value && newFlashcards.length > 0) {
    sessionFlashcards.value[sessionId.value] = [...newFlashcards]
  }
})

function triggerUpload() {
  fileInput.value?.click()
}

async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files) return

  for (const file of target.files) {
    addDocument(file)
    const ext = file.name.toLowerCase()
    if (ext.endsWith('.txt') || ext.endsWith('.md') || ext.endsWith('.pdf')) {
      await ingestDocument(documents.value.length - 1)
    }
  }
  if (fileInput.value) fileInput.value.value = ''
}

function getFileIcon(doc: Document): string {
  const name = doc.file.name.toLowerCase()
  if (name.endsWith('.pdf')) return 'i-lucide-file-text'
  if (name.endsWith('.md')) return 'i-lucide-file-code'
  return 'i-lucide-file'
}

function getStatusIcon(doc: Document): string | null {
  const icons: Record<string, string> = {
    ingesting: 'i-lucide-loader-2',
    ingested: 'i-lucide-check-circle',
    error: 'i-lucide-alert-circle'
  }
  return icons[doc.status] || null
}

function getStatusClass(doc: Document): string {
  return `status-${doc.status}`
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<template>
  <div class="documents-panel">
    <div class="panel-header">
      <h2 class="panel-title">Sources</h2>
    </div>
    
    <div class="upload-section">
      <input
        ref="fileInput"
        type="file"
        accept=".pdf,.txt,.md"
        multiple
        class="hidden-input"
        @change="handleFileChange"
      >
      <UButton
        icon="i-lucide-plus"
        color="primary"
        variant="soft"
        block
        @click="triggerUpload"
      >
        Add source
      </UButton>
      
      <!-- Flashcard Count Selector -->
      <div class="flashcard-count-section">
        <label class="count-label">Number of flashcards</label>
        <div class="count-input-wrapper">
          <UButton
            icon="i-lucide-minus"
            color="neutral"
            variant="ghost"
            size="xs"
            :disabled="flashcardCount <= FLASHCARD_COUNT_MIN"
            @click="flashcardCount = Math.max(FLASHCARD_COUNT_MIN, flashcardCount - 1)"
          />
          <input
            v-model.number="flashcardCount"
            type="number"
            :min="FLASHCARD_COUNT_MIN"
            :max="FLASHCARD_COUNT_MAX"
            class="count-input"
            @blur="flashcardCount = Math.min(FLASHCARD_COUNT_MAX, Math.max(FLASHCARD_COUNT_MIN, flashcardCount || FLASHCARD_COUNT_MIN))"
          />
          <UButton
            icon="i-lucide-plus"
            color="neutral"
            variant="ghost"
            size="xs"
            :disabled="flashcardCount >= FLASHCARD_COUNT_MAX"
            @click="flashcardCount = Math.min(FLASHCARD_COUNT_MAX, flashcardCount + 1)"
          />
        </div>
      </div>

      <!-- View existing flashcards (no new request) -->
      <UButton
        v-if="hasFlashcards"
        icon="i-lucide-eye"
        color="primary"
        variant="soft"
        block
        class="flashcard-button"
        @click="openFlashcardPanel"
      >
        View Flashcards ({{ currentFlashcardCount }})
      </UButton>

      <!-- Generate new flashcards -->
      <UButton
        icon="i-lucide-layers"
        color="primary"
        :variant="hasFlashcards ? 'outline' : 'solid'"
        block
        class="flashcard-button"
        :loading="isGeneratingFlashcards"
        :disabled="!hasIngestedDocuments"
        @click="generateFlashcards"
      >
        {{ hasFlashcards ? 'Regenerate' : 'Generate Flashcards' }}
      </UButton>
    </div>
    
    <div class="documents-list">
      <div
        v-for="(doc, index) in documents"
        :key="index"
        class="document-item"
        :class="getStatusClass(doc)"
      >
        <UIcon :name="getFileIcon(doc)" class="doc-icon" />
        <div class="doc-info">
          <div class="doc-name">{{ doc.file.name }}</div>
          <div class="doc-meta">
            {{ formatSize(doc.file.size) }}
            <span v-if="doc.status === 'ingested'" class="chunk-info">
              · {{ doc.chunksIngested }} chunks
            </span>
            <span v-if="doc.status === 'error'" class="error-info" :title="doc.error">
              · Error
            </span>
          </div>
        </div>
        <UIcon 
          v-if="getStatusIcon(doc)" 
          :name="getStatusIcon(doc)!" 
          class="status-icon"
          :class="{ 'animate-spin': doc.status === 'ingesting' }"
        />
        <UButton
          icon="i-lucide-x"
          color="neutral"
          variant="ghost"
          size="xs"
          @click="removeDocument(index)"
        />
      </div>
      
      <div v-if="documents.length === 0" class="empty-state">
        <UIcon name="i-lucide-folder-open" class="empty-icon" />
        <p>No sources added yet</p>
        <p class="empty-hint">Upload PDF, TXT, or MD files</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.documents-panel {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background-color: var(--ui-bg-muted);
  border-right: 1px solid var(--ui-border);
  min-height: 0;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid var(--ui-border);
  flex-shrink: 0;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ui-text);
  margin: 0;
}

.upload-section {
  padding: 12px 16px;
  flex-shrink: 0;
}

.flashcard-button {
  margin-top: 8px;
}

.flashcard-count-section {
  margin-top: 12px;
  padding: 10px 12px;
  background-color: var(--ui-bg);
  border-radius: 8px;
  border: 1px solid var(--ui-border);
}

.count-label {
  display: block;
  font-size: 11px;
  font-weight: 500;
  color: var(--ui-text-muted);
  margin-bottom: 8px;
}

.count-input-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.count-input {
  width: 48px;
  text-align: center;
  padding: 4px 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--ui-text);
  background-color: var(--ui-bg-elevated);
  border: 1px solid var(--ui-border);
  border-radius: 6px;
  -moz-appearance: textfield;
}

.count-input::-webkit-outer-spin-button,
.count-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.count-input:focus {
  outline: none;
  border-color: var(--ui-primary);
}

.hidden-input {
  display: none;
}

.documents-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  min-height: 0;
}

.document-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background-color: var(--ui-bg);
  margin-bottom: 6px;
  transition: background-color 0.15s;
}

.document-item:hover {
  background-color: var(--ui-bg-elevated);
}

.doc-icon {
  font-size: 18px;
  color: var(--ui-text-muted);
  flex-shrink: 0;
}

.doc-info {
  flex: 1;
  min-width: 0;
}

.doc-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--ui-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-meta {
  font-size: 11px;
  color: var(--ui-text-muted);
  margin-top: 2px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: var(--ui-text-muted);
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 13px;
}

.empty-hint {
  margin-top: 4px !important;
  font-size: 11px !important;
  opacity: 0.7;
}

.status-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.status-ingesting .status-icon {
  color: var(--ui-primary);
}

.status-ingested .status-icon {
  color: #22c55e;
}

.status-error .status-icon {
  color: #ef4444;
}

.chunk-info {
  color: #22c55e;
}

.error-info {
  color: #ef4444;
  cursor: help;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
