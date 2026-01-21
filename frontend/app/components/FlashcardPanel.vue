<script setup lang="ts">
import type { Flashcard, Citation, CitationsMap } from '~/composables/useAppState'

const { flashcards, citations, isFlashcardPanelOpen, isGeneratingFlashcards, closeFlashcardPanel } = useAppState()

const currentIndex = ref(0)
const isFlipped = ref(false)
const panelRef = ref<HTMLElement | null>(null)
const activeCitation = ref<Citation | null>(null)
const showCitationPopover = ref(false)

const currentCard = computed<Flashcard | undefined>(() => flashcards.value[currentIndex.value])
const totalCards = computed(() => flashcards.value.length)
const hasCards = computed(() => totalCards.value > 0)
const canGoPrev = computed(() => currentIndex.value > 0)
const canGoNext = computed(() => currentIndex.value < totalCards.value - 1)

const currentCardCitation = computed<Citation | null>(() => {
  const card = currentCard.value
  if (!card?.citation) return null
  return citations.value[card.citation] || null
})

interface AnswerSegment {
  type: 'text' | 'citation'
  content: string
  citation?: Citation
}

function parseAnswerWithCitations(answer: string, citationsMap: CitationsMap): AnswerSegment[] {
  const segments: AnswerSegment[] = []
  const regex = /\[(\d+)\]/g
  let lastIndex = 0
  let match

  while ((match = regex.exec(answer)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', content: answer.slice(lastIndex, match.index) })
    }
    segments.push({ type: 'citation', content: match[0], citation: citationsMap[match[0]] })
    lastIndex = regex.lastIndex
  }

  if (lastIndex < answer.length) {
    segments.push({ type: 'text', content: answer.slice(lastIndex) })
  }

  return segments.length > 0 ? segments : [{ type: 'text', content: answer }]
}

const answerSegments = computed(() => {
  if (!currentCard.value?.answer) return []
  return parseAnswerWithCitations(currentCard.value.answer, citations.value)
})

function showCitationDetails(citation: Citation | undefined) {
  if (!citation) return
  activeCitation.value = citation
  showCitationPopover.value = true
}

function hideCitationDetails() {
  showCitationPopover.value = false
  activeCitation.value = null
}

function nextCard() {
  if (!canGoNext.value) return
  currentIndex.value++
  isFlipped.value = false
  hideCitationDetails()
}

function prevCard() {
  if (!canGoPrev.value) return
  currentIndex.value--
  isFlipped.value = false
  hideCitationDetails()
}

function flipCard() {
  isFlipped.value = !isFlipped.value
}

function handleClose() {
  closeFlashcardPanel()
  currentIndex.value = 0
  isFlipped.value = false
  hideCitationDetails()
}

function handleClickOutside(event: MouseEvent) {
  if (panelRef.value && !panelRef.value.contains(event.target as Node)) {
    handleClose()
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (!isFlashcardPanelOpen.value) return

  switch (event.key) {
    case 'Escape': handleClose(); break
    case 'ArrowLeft': prevCard(); break
    case 'ArrowRight': nextCard(); break
    case ' ':
    case 'Enter':
      event.preventDefault()
      flipCard()
      break
  }
}

onMounted(() => document.addEventListener('keydown', handleKeydown))
onUnmounted(() => document.removeEventListener('keydown', handleKeydown))

watch(isFlashcardPanelOpen, (isOpen) => {
  if (isOpen) {
    currentIndex.value = 0
    isFlipped.value = false
    hideCitationDetails()
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="panel">
      <div
        v-if="isFlashcardPanelOpen"
        class="panel-overlay"
        @click="handleClickOutside"
      >
        <div ref="panelRef" class="flashcard-panel">
          <!-- Header -->
          <div class="panel-header">
            <h2 class="panel-title">
              <UIcon name="i-lucide-layers" class="title-icon" />
              Flashcards
            </h2>
            <UButton
              icon="i-lucide-x"
              color="neutral"
              variant="ghost"
              size="sm"
              @click="handleClose"
            />
          </div>

          <!-- Content -->
          <div class="panel-content">
            <!-- Loading State -->
            <div v-if="isGeneratingFlashcards" class="loading-state">
              <UIcon name="i-lucide-loader-2" class="loading-spinner" />
              <p>Generating flashcards...</p>
            </div>

            <!-- Empty State -->
            <div v-else-if="!hasCards" class="empty-state">
              <UIcon name="i-lucide-layers" class="empty-icon" />
              <p>No flashcards generated</p>
              <p class="empty-hint">Generate flashcards from your documents</p>
            </div>

            <!-- Flashcard Carousel -->
            <div v-else class="carousel">
              <!-- Card Counter -->
              <div class="card-counter">
                {{ currentIndex + 1 }} of {{ totalCards }}
              </div>

              <!-- Card Container -->
              <div
                class="card-container"
                :class="{ flipped: isFlipped }"
              >
                <div class="card">
                  <!-- Front (Question) -->
                  <div class="card-face card-front">
                    <div class="card-label">Question</div>
                    <div class="card-content">{{ currentCard?.question }}</div>
                  </div>

                  <!-- Back (Answer) -->
                  <div class="card-face card-back">
                    <div class="card-label">Answer</div>
                    <div class="card-content answer-content">
                      <!-- Display answer text with any inline citations -->
                      <template v-for="(segment, idx) in answerSegments" :key="idx">
                        <span v-if="segment.type === 'text'">{{ segment.content }}</span>
                        <UTooltip
                          v-else-if="segment.type === 'citation' && segment.citation"
                          :text="`${segment.citation.source} (p.${segment.citation.page})`"
                        >
                          <span
                            class="citation-badge"
                            @click.stop="showCitationDetails(segment.citation)"
                          >
                            {{ segment.content }}
                          </span>
                        </UTooltip>
                        <span v-else class="citation-badge citation-unknown">{{ segment.content }}</span>
                      </template>
                      
                      <!-- If citation field exists and wasn't inline, append it -->
                      <template v-if="currentCard?.citation && currentCardCitation && !currentCard.answer.includes(currentCard.citation)">
                        <span> </span>
                        <UTooltip :text="`${currentCardCitation.source} (p.${currentCardCitation.page})`">
                          <span
                            class="citation-badge"
                            @click.stop="showCitationDetails(currentCardCitation)"
                          >
                            {{ currentCard.citation }}
                          </span>
                        </UTooltip>
                      </template>
                    </div>

                    <!-- Source Footer -->
                    <div v-if="currentCardCitation" class="source-footer">
                      <UIcon name="i-lucide-file-text" class="source-icon" />
                      <span class="source-text">
                        {{ currentCardCitation.source }} · Page {{ currentCardCitation.page }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Citation Detail Modal -->
              <UModal v-model:open="showCitationPopover">
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

              <!-- Navigation -->
              <div class="card-navigation">
                <UButton
                  icon="i-lucide-chevron-left"
                  color="neutral"
                  variant="soft"
                  :disabled="!canGoPrev"
                  @click.stop="prevCard"
                />
                <UButton
                  icon="i-lucide-arrow-left-right"
                  color="primary"
                  variant="soft"
                  @click.stop="flipCard"
                />
                <UButton
                  icon="i-lucide-chevron-right"
                  color="neutral"
                  variant="soft"
                  :disabled="!canGoNext"
                  @click.stop="nextCard"
                />
              </div>

              <!-- Keyboard hints -->
              <div class="keyboard-hints">
                <span>←/→ Navigate</span>
                <span>Space Flip</span>
                <span>Esc Close</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.panel-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  justify-content: flex-end;
}

.flashcard-panel {
  width: 320px;
  height: 100%;
  background-color: var(--ui-bg);
  border-left: 1px solid var(--ui-border);
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--ui-border);
  flex-shrink: 0;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--ui-text);
  margin: 0;
}

.title-icon {
  font-size: 18px;
  color: var(--ui-primary);
}

.panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  min-height: 0;
  overflow-y: auto;
}

.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--ui-text-muted);
}

.loading-spinner {
  font-size: 32px;
  color: var(--ui-primary);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--ui-text-muted);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.4;
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

.carousel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-counter {
  text-align: center;
  font-size: 12px;
  font-weight: 500;
  color: var(--ui-text-muted);
}

.card-container {
  flex: 1;
  perspective: 1000px;
  min-height: 200px;
}

.card {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 200px;
  transform-style: preserve-3d;
  transition: transform 0.5s ease;
}

.card-container.flipped .card {
  transform: rotateY(180deg);
}

.card-face {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  padding: 20px;
  border-radius: 12px;
  backface-visibility: hidden;
  border: 1px solid var(--ui-border);
}

.card-front {
  background-color: var(--ui-bg-elevated);
}

.card-back {
  background-color: var(--ui-bg-muted);
  transform: rotateY(180deg);
}

.card-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--ui-primary);
  margin-bottom: 12px;
}

.card-content {
  flex: 1;
  font-size: 14px;
  line-height: 1.6;
  color: var(--ui-text);
  overflow-y: auto;
}

.card-hint {
  font-size: 11px;
  color: var(--ui-text-muted);
  text-align: center;
  margin-top: 12px;
  opacity: 0.7;
}

.card-navigation {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.keyboard-hints {
  display: flex;
  justify-content: center;
  gap: 16px;
  font-size: 10px;
  color: var(--ui-text-muted);
  opacity: 0.6;
}

.keyboard-hints span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.answer-content {
  display: inline;
}

.citation-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 1px 6px;
  margin: 0 1px;
  font-size: 11px;
  font-weight: 600;
  color: var(--ui-primary);
  background-color: color-mix(in srgb, var(--ui-primary) 15%, transparent);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
  vertical-align: baseline;
}

.citation-badge:hover {
  background-color: color-mix(in srgb, var(--ui-primary) 25%, transparent);
  transform: translateY(-1px);
}

.citation-badge.citation-unknown {
  color: var(--ui-text-muted);
  background-color: var(--ui-bg-elevated);
  cursor: default;
}

.citation-badge.citation-unknown:hover {
  transform: none;
}

.source-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--ui-border);
  font-size: 11px;
  color: var(--ui-text-muted);
}

.source-icon {
  font-size: 14px;
  flex-shrink: 0;
  color: var(--ui-primary);
  opacity: 0.7;
}

.source-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.citation-modal {
  padding: 16px;
  min-width: 280px;
  max-width: 400px;
}

.citation-modal-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--ui-border);
}

.citation-modal-icon {
  font-size: 18px;
  color: var(--ui-primary);
}

.citation-modal-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ui-text);
}

.citation-modal-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.citation-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.citation-meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--ui-text-muted);
}

.citation-meta-item i,
.citation-meta-item svg {
  font-size: 14px;
  color: var(--ui-primary);
  opacity: 0.7;
}

.citation-text-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--ui-text-muted);
  margin-top: 4px;
}

.citation-text {
  font-size: 13px;
  line-height: 1.6;
  color: var(--ui-text);
  background-color: var(--ui-bg-elevated);
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--ui-border);
  max-height: 150px;
  overflow-y: auto;
}

.citation-modal-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--ui-border);
}

.panel-enter-active,
.panel-leave-active {
  transition: opacity 0.2s ease;
}

.panel-enter-active .flashcard-panel,
.panel-leave-active .flashcard-panel {
  transition: transform 0.3s ease;
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
}

.panel-enter-from .flashcard-panel,
.panel-leave-to .flashcard-panel {
  transform: translateX(100%);
}
</style>
