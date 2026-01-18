<script setup lang="ts">
import type { Document } from '~/composables/useAppState'

const {
  documents,
  addDocument,
  removeDocument,
  ingestDocument,
  hasIngestedDocuments,
  isGeneratingFlashcards,
  generateFlashcards
} = useAppState()


const fileInput = ref<HTMLInputElement | null>(null)

function triggerUpload() {
  fileInput.value?.click()
}

async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (files) {
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      if (file) {
        addDocument(file)
        // Auto-ingest supported files (PDF, TXT, MD)
        const name = file.name.toLowerCase()
        if (name.endsWith('.txt') || name.endsWith('.md') || name.endsWith('.pdf')) {
          const index = documents.value.length - 1
          await ingestDocument(index)
        }
      }
    }
  }
  // Reset input so same file can be selected again
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

function getFileIcon(doc: Document): string {
  const name = doc.file.name.toLowerCase()
  if (name.endsWith('.pdf')) return 'i-lucide-file-text'
  if (name.endsWith('.md')) return 'i-lucide-file-code'
  if (name.endsWith('.txt')) return 'i-lucide-file'
  return 'i-lucide-file'
}

function getStatusIcon(doc: Document): string | null {
  switch (doc.status) {
    case 'ingesting': return 'i-lucide-loader-2'
    case 'ingested': return 'i-lucide-check-circle'
    case 'error': return 'i-lucide-alert-circle'
    default: return null
  }
}

function getStatusClass(doc: Document): string {
  switch (doc.status) {
    case 'ingesting': return 'status-ingesting'
    case 'ingested': return 'status-ingested'
    case 'error': return 'status-error'
    default: return 'status-pending'
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
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
      <UButton
        icon="i-lucide-layers"
        color="primary"
        variant="outline"
        block
        class="flashcard-button"
        :loading="isGeneratingFlashcards"
        :disabled="!hasIngestedDocuments"
        @click="generateFlashcards"
      >
        Generate Flashcards
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
  /* CRITICAL: min-height: 0 allows flex child to shrink and enable scrolling */
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

.hidden-input {
  display: none;
}

.documents-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  /* CRITICAL: min-height: 0 enables scrolling in flex child */
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

/* Status indicator styles */
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
