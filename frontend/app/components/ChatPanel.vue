<script setup lang="ts">
const { messages, currentPrompt, addMessage, clearPrompt, getDocumentMetadata } = useAppState()

const isLoading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

async function sendMessage() {
  const prompt = currentPrompt.value.trim()
  if (!prompt || isLoading.value) return
  
  // Add user message immediately
  addMessage('user', prompt)
  clearPrompt()
  
  // Scroll to bottom after adding user message
  await nextTick()
  scrollToBottom()
  
  // Send to API
  isLoading.value = true
  try {
    const response = await $fetch('/api/summarize', {
      method: 'POST',
      body: {
        prompt,
        documents: getDocumentMetadata()
      }
    })
    
    addMessage('assistant', response.response)
  } catch (error) {
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
          {{ msg.content }}
        </div>
      </div>
      
      <div v-if="isLoading" class="message-wrapper assistant">
        <div class="message-bubble assistant loading">
          <UIcon name="i-lucide-loader-2" class="loading-icon" />
          Thinking...
        </div>
      </div>
    </div>
    
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
  /* CRITICAL: min-height: 0 allows flex child to shrink and enable scrolling */
  min-height: 0;
  background-color: var(--ui-bg);
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  /* CRITICAL: min-height: 0 enables scrolling in flex child */
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
</style>
