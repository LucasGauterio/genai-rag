<script setup lang="ts">
import type { Message, CitationsMap, Citation } from '~/composables/useAppState'

const { messages, currentPrompt, addMessage, clearPrompt, getDocumentMetadata, sessionId, hasIngestedDocuments } = useAppState()

const isLoading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const activeCitation = ref<Citation | null>(null)
const showCitationModal = ref(false)

interface MessageSegment {
  type: 'text' | 'citation'
  content: string
  citation?: Citation
}

interface SummarizeResponse {
  response: string
  citations?: CitationsMap
  chunksUsed?: number
}

function parseMessageWithCitations(content: string, citations?: CitationsMap): MessageSegment[] {
  if (!citations || Object.keys(citations).length === 0) {
    return [{ type: 'text', content }]
  }

  const segments: MessageSegment[] = []
  const regex = /\[(\d+)\]/g
  let lastIndex = 0
  let match

  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', content: content.slice(lastIndex, match.index) })
    }
    segments.push({ type: 'citation', content: match[0], citation: citations[match[0]] })
    lastIndex = regex.lastIndex
  }

  if (lastIndex < content.length) {
    segments.push({ type: 'text', content: content.slice(lastIndex) })
  }

  return segments
}

function showCitationDetails(citation: Citation | undefined) {
  if (!citation) return
  activeCitation.value = citation
  showCitationModal.value = true
}

function hideCitationDetails() {
  showCitationModal.value = false
  activeCitation.value = null
}

async function sendMessage() {
  const prompt = currentPrompt.value.trim()
  if (!prompt || isLoading.value) return

  if (!sessionId.value || !hasIngestedDocuments.value) {
    addMessage('assistant', 'Please upload and ingest documents first before asking questions.')
    return
  }

  addMessage('user', prompt)
  clearPrompt()

  await nextTick()
  scrollToBottom()

  isLoading.value = true
  try {
    const response = await $fetch<SummarizeResponse>('/api/summarize', {
      method: 'POST',
      body: {
        prompt,
        sessionId: sessionId.value,
        documents: getDocumentMetadata()
      }
    })
    addMessage('assistant', response.response, response.citations)
  } catch {
    addMessage('assistant', 'Sorry, there was an error processing your request.')
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}
</script>

<template>
  <div class="chat-panel">
    <div ref="messagesContainer" class="messages-area">
      <div v-if="messages.length === 0" class="welcome-message">
        <UIcon name="i-lucide-message-square" class="welcome-icon" />
        <h2>Start a conversation</h2>
        <p>Upload documents and ask questions about them</p>
      </div>
      
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="message-wrapper"
        :class="msg.role"
      >
        <div class="message-bubble" :class="msg.role">
          <!-- User messages: plain text -->
          <template v-if="msg.role === 'user'">{{ msg.content }}</template>
          
          <!-- Assistant messages: parse citations -->
          <template v-else>
            <template v-for="(segment, segIdx) in parseMessageWithCitations(msg.content, msg.citations)" :key="segIdx">
              <span v-if="segment.type === 'text'">{{ segment.content }}</span>
              <UTooltip
                v-else-if="segment.type === 'citation' && segment.citation"
                :text="`${segment.citation.source} (p.${segment.citation.page})`"
              >
                <span
                  class="citation-badge"
                  @click="showCitationDetails(segment.citation)"
                >
                  {{ segment.content }}
                </span>
              </UTooltip>
              <span v-else class="citation-badge citation-unknown">{{ segment.content }}</span>
            </template>
          </template>
        </div>
      </div>
      
      <div v-if="isLoading" class="message-wrapper assistant">
        <div class="message-bubble assistant loading">
          <UIcon name="i-lucide-loader-2" class="loading-icon" />
          Thinking...
        </div>
      </div>
    </div>

    <!-- Citation Detail Modal -->
    <UModal v-model:open="showCitationModal">
      <template #content>
        <div class="citation-modal">
          <div class="citation-modal-header">
            <UIcon name="i-lucide-quote" class="citation-modal-icon" />
            <span class="citation-modal-title">Source Citation</span>
          </div>
          <div v-if="activeCitation" class="citation-modal-body">
            <div class="citation-meta">
              <div class="citation-meta-item">
                <UIcon name="i-lucide-file-text" />
                <span>{{ activeCitation.source }}</span>
              </div>
              <div class="citation-meta-item">
                <UIcon name="i-lucide-bookmark" />
                <span>Page {{ activeCitation.page }}</span>
              </div>
            </div>
            <div class="citation-text-label">Excerpt:</div>
            <div class="citation-text">
              {{ activeCitation.text }}
            </div>
          </div>
          <div class="citation-modal-footer">
            <UButton
              color="neutral"
              variant="soft"
              size="sm"
              @click="hideCitationDetails"
            >
              Close
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
    
    <div class="input-area">
      <div class="input-container">
        <UTextarea
          v-model="currentPrompt"
          placeholder="Ask about your documents..."
          :rows="1"
          autoresize
          :maxrows="5"
          class="message-input"
          @keydown="handleKeydown"
        />
        <UButton
          icon="i-lucide-send"
          color="primary"
          :disabled="!currentPrompt.trim() || isLoading"
          :loading="isLoading"
          @click="sendMessage"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background-color: var(--ui-bg);
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  min-height: 0;
}

.welcome-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: var(--ui-text-muted);
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.4;
}

.welcome-message h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: var(--ui-text);
}

.welcome-message p {
  font-size: 14px;
  margin: 0;
}

.message-wrapper {
  display: flex;
  margin-bottom: 16px;
}

.message-wrapper.user {
  justify-content: flex-end;
}

.message-wrapper.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-bubble.user {
  background-color: var(--ui-primary);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-bubble.assistant {
  background-color: var(--ui-bg-muted);
  color: var(--ui-text);
  border-bottom-left-radius: 4px;
}

.message-bubble.loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ui-text-muted);
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.input-area {
  flex-shrink: 0;
  padding: 16px 24px 24px;
  background-color: var(--ui-bg);
  border-top: 1px solid var(--ui-border);
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  max-width: 800px;
  margin: 0 auto;
}

.message-input {
  flex: 1;
}

.citation-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 18px;
  padding: 0 4px;
  margin: 0 2px;
  font-size: 10px;
  font-weight: 600;
  color: var(--ui-primary);
  background-color: var(--ui-primary-alpha-10);
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.15s;
  vertical-align: middle;
}

.citation-badge:hover {
  background-color: var(--ui-primary-alpha-20);
}

.citation-unknown {
  color: var(--ui-text-muted);
  background-color: var(--ui-bg-elevated);
}

.citation-modal {
  padding: 20px;
  background: var(--ui-bg);
  border-radius: 12px;
  min-width: 320px;
  max-width: 500px;
}

.citation-modal-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--ui-border);
}

.citation-modal-icon {
  font-size: 20px;
  color: var(--ui-primary);
}

.citation-modal-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--ui-text);
}

.citation-modal-body {
  margin-bottom: 16px;
}

.citation-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}

.citation-meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--ui-text-muted);
}

.citation-text-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--ui-text-muted);
  margin-bottom: 6px;
}

.citation-text {
  font-size: 13px;
  line-height: 1.5;
  color: var(--ui-text);
  background: var(--ui-bg-muted);
  padding: 12px;
  border-radius: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.citation-modal-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--ui-border);
}
</style>
