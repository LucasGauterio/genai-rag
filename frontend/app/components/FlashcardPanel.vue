<script setup lang="ts">
import type { Flashcard } from '~/composables/useAppState'

const { flashcards, isFlashcardPanelOpen, isGeneratingFlashcards, closeFlashcardPanel } = useAppState()

// Local state
const currentIndex = ref(0)
const isFlipped = ref(false)
const panelRef = ref<HTMLElement | null>(null)

// Computed
const currentCard = computed<Flashcard | undefined>(() => flashcards.value[currentIndex.value])
const totalCards = computed(() => flashcards.value.length)
const hasCards = computed(() => totalCards.value > 0)
const canGoPrev = computed(() => currentIndex.value > 0)
const canGoNext = computed(() => currentIndex.value < totalCards.value - 1)

// Methods
function nextCard() {
  if (canGoNext.value) {
    currentIndex.value++
    isFlipped.value = false
  }
}

function prevCard() {
  if (canGoPrev.value) {
    currentIndex.value--
    isFlipped.value = false
  }
}

function flipCard() {
  isFlipped.value = !isFlipped.value
}

function handleClose() {
  closeFlashcardPanel()
  // Reset state when closing
  currentIndex.value = 0
  isFlipped.value = false
}

function handleClickOutside(event: MouseEvent) {
  if (panelRef.value && !panelRef.value.contains(event.target as Node)) {
    handleClose()
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (!isFlashcardPanelOpen.value) return

  switch (event.key) {
    case 'Escape':
      handleClose()
      break
    case 'ArrowLeft':
      prevCard()
      break
    case 'ArrowRight':
      nextCard()
      break
    case ' ':
    case 'Enter':
      event.preventDefault()
      flipCard()
      break
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// Reset state when panel opens
watch(isFlashcardPanelOpen, (isOpen) => {
  if (isOpen) {
    currentIndex.value = 0
    isFlipped.value = false
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
                @click="flipCard"
              >
                <div class="card">
                  <!-- Front (Question) -->
                  <div class="card-face card-front">
                    <div class="card-label">Question</div>
                    <div class="card-content">{{ currentCard?.question }}</div>
                    <div class="card-hint">Click to reveal answer</div>
                  </div>

                  <!-- Back (Answer) -->
                  <div class="card-face card-back">
                    <div class="card-label">Answer</div>
                    <div class="card-content">{{ currentCard?.answer }}</div>
                    <div class="card-hint">Click to see question</div>
                  </div>
                </div>
              </div>

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

/* Loading State */
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

/* Empty State */
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

/* Carousel */
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

/* Card Container - 3D Flip */
.card-container {
  flex: 1;
  perspective: 1000px;
  cursor: pointer;
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

/* Navigation */
.card-navigation {
  display: flex;
  justify-content: center;
  gap: 12px;
}

/* Keyboard Hints */
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

/* Panel Transition */
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
