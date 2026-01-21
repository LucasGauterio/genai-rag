<template>
  <div class="session-panel" :class="{ 'collapsed': !expanded }">
    <div class="panel-header">
      <h2 class="panel-title">Sessions</h2>
      <div class="header-actions">
        <UTooltip :text="expanded ? 'Collapse sessions panel' : 'Expand sessions panel'">
          <UButton 
            :icon="expanded ? 'i-heroicons-chevron-left' : 'i-heroicons-chat-bubble-left-right'"
            color="gray"
            variant="solid"
            size="xs"
            @click="toggleExpanded"
            :ui="{ base: 'cursor-pointer' }"
          />
        </UTooltip>
        <UTooltip v-if=expanded text="Refresh sessions">
          <UButton
            icon='i-heroicons-arrow-path'
            color="gray"
            variant="solid"
            size="xs"
            @click="fetchSessions"
            :ui="{ base: 'cursor-pointer' }"
          />
        </UTooltip>
      </div>
    </div>
    
    <div v-show="expanded" class="sessions-list">
      <div 
        v-for="session in sessions" 
        :key="session.session_id"
        class="session-item"
        :class="{ 'selected': selectedSessionId === session.session_id }"
        @click="selectSession(session.session_id)"
      >
        <div class="selected-indicator" v-if="selectedSessionId === session.session_id"></div>
        <div class="session-info">
          <h3 class="session-name">{{ session.name || `Session ${session.session_id.substring(0, 6)}` }}</h3>
          <p class="session-meta">{{ formatDate(session.created_at) }}</p>
          <p class="session-chunk-count">{{ session.chunk_count ?? 0 }} chunks</p>
        </div>
        <UIcon 
          v-if="selectedSessionId === session.session_id"
          :name="getStatusIcon(sessionLoadState)"
          class="status-icon"
          :class="{ 'animate-spin': sessionLoadState === 'loading' }"
        />
        <UTooltip
          :text="sessions.length <= 1 
            ? 'At least one session must remain' 
            : 'Delete this session'"
          >
          <UButton
            icon="i-heroicons-trash"
            color="red"
            variant="ghost"
            size="xs"
            @click.stop="deleteSession(session.session_id)"
            :disabled="sessions.length <= 1"
            :ui="{ base: 'cursor-pointer disabled:cursor-not-allowed' }"
          />
        </UTooltip>
      </div>
      
      <div v-if="sessions.length === 0" class="empty-state">
        <UIcon name="i-heroicons-document-text" class="empty-icon" />
        <p>No sessions created yet</p>
      </div>
    </div>
    
    <div v-show="expanded" class="panel-footer">
      <UButton 
        icon="i-heroicons-plus" 
        color="primary"
        variant="soft"
        block
        @click="createSession"
        :loading="creatingSession"
        class="create-btn"
      >
        New Session
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
const { sessionId: selectedSessionId, sessionLoadState } = useAppState()

interface Session {
  session_id: string
  name?: string
  created_at: string
  chunk_count?: number
}

const sessions = ref<Session[]>([])
const creatingSession = ref(false)
const expanded = ref(true)

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
}

function getStatusIcon(state: string): string {
  const icons: Record<string, string> = {
    error: 'i-lucide-alert-circle',
    loading: 'i-lucide-loader-2',
    idle: 'i-lucide-check-circle'
  }
  return icons[state] || 'i-lucide-check-circle'
}

async function fetchSessions() {
  try {
    const response = await $fetch<{ sessions?: Session[] } | Session[]>('/api/sessions')
    sessions.value = Array.isArray(response) ? response : (response.sessions || [])
    sessions.value.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    if (sessions.value.length > 0 && !selectedSessionId.value) {
      selectedSessionId.value = sessions.value[0].session_id
    } else if (sessions.value.length === 0) {
      createSession()
    }
  } catch (err) {
    console.error('Failed to fetch sessions:', err)
  }
}

async function createSession() {
  creatingSession.value = true
  try {
    const response = await $fetch<Session>('/api/sessions', { method: 'POST' })
    sessions.value.unshift(response)
    selectedSessionId.value = response.session_id
  } catch (err) {
    console.error('Failed to create session:', err)
  } finally {
    creatingSession.value = false
    fetchSessions()
  }
}

function selectSession(sessionId: string) {
  selectedSessionId.value = sessionId
}

async function deleteSession(sessionId: string) {
  if (sessions.value.length <= 1) return

  try {
    await $fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' })
    sessions.value = sessions.value.filter(s => s.session_id !== sessionId)
    if (selectedSessionId.value === sessionId) {
      selectedSessionId.value = sessions.value[0]?.session_id || null
    }
  } catch (err) {
    console.error('Failed to delete session:', err)
  } finally {
    fetchSessions()
  }
}

function toggleExpanded() {
  expanded.value = !expanded.value
}

onMounted(fetchSessions)
</script>

<style scoped>
.session-panel {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background-color: var(--ui-bg-muted);
  border-right: 1px solid var(--ui-primary);
  min-height: 0;
  overflow: hidden;
  transition: width 0.2s ease;
}

.session-panel.collapsed {
  width: 48px;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid var(--ui-border);
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ui-text);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 4px;
}

.create-btn {
  padding: 4px 8px;
}

.sessions-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  min-height: 0;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-radius: 8px;
  background-color: var(--ui-bg);
  margin-bottom: 6px;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
  position: relative;
}

.session-item:hover {
  background-color: var(--ui-bg-elevated);
  transform: translateX(4px);
}

.session-item.selected {
  background-color: var(--ui-bg-accent);
  border: 1px solid var(--ui-border-accent);
  box-shadow: 0 0 0 1px var(--ui-border-accent);
}

.selected-indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: var(--ui-primary);
  border-radius: 0 3px 3px 0;
}

.session-info {
  flex: 1;
  min-width: 0;
  padding-left: 8px;
}

.session-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--ui-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.session-meta {
  font-size: 11px;
  color: var(--ui-text-muted);
}

.session-chunk-count {
  font-size: 11px;
  color: #22c55e;
  margin-top: 2px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  text-align: center;
  color: var(--ui-text-muted);
  margin-top: 10px;
}

.empty-icon {
  font-size: 24px;
  margin-bottom: 8px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 13px;
}

.panel-footer {
  padding: 12px 16px;
  flex-shrink: 0;
  border-top: 1px solid var(--ui-border);
}

.session-panel.collapsed .panel-title,
.session-panel.collapsed .sessions-list,
.session-panel.collapsed .panel-footer {
  display: none;
}

.session-panel.collapsed .header-actions {
  justify-content: center;
  width: 100%;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

.status-icon {
  font-size: 16px;
  flex-shrink: 0;
}

</style>