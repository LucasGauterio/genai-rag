import { ref, computed } from 'vue'

interface Message {
    role: 'user' | 'assistant'
    content: string
}

export interface Document {
    file: File
    status: 'pending' | 'ingesting' | 'ingested' | 'error'
    error?: string
    chunksIngested?: number
}

export interface Flashcard {
    id: string
    question: string
    answer: string
    citation?: string
}

// Shared state - in-memory only, clears on reload
const messages = ref<Message[]>([])
const currentPrompt = ref('')
const documents = ref<Document[]>([])

// Session state - tracks current backend session
const sessionId = ref<string | null>(null)

// Flashcard state
const flashcards = ref<Flashcard[]>([])
const isFlashcardPanelOpen = ref(false)
const isGeneratingFlashcards = ref(false)

export function useAppState() {
    // Computed: check if at least one document is ingested
    const hasIngestedDocuments = computed(() =>
        documents.value.some(d => d.status === 'ingested')
    )

    /**
     * Ensure a session exists. Creates one if needed.
     * Returns the session ID.
     */
    async function ensureSession(): Promise<string> {
        if (sessionId.value) {
            return sessionId.value
        }

        // Create a new session via the backend
        const response = await $fetch<{ session_id: string }>('/api/sessions', {
            method: 'POST'
        })

        sessionId.value = response.session_id
        return response.session_id
    }

    function addMessage(role: 'user' | 'assistant', content: string) {
        messages.value.push({ role, content })
    }

    function addDocument(file: File) {
        documents.value.push({
            file,
            status: 'pending'
        })
    }

    function removeDocument(index: number) {
        documents.value.splice(index, 1)
    }

    function updateDocumentStatus(
        index: number,
        status: Document['status'],
        metadata?: { error?: string; chunksIngested?: number }
    ) {
        if (index >= 0 && index < documents.value.length) {
            const doc = documents.value[index]!
            doc.status = status
            if (metadata?.error) {
                doc.error = metadata.error
            }
            if (metadata?.chunksIngested !== undefined) {
                doc.chunksIngested = metadata.chunksIngested
            }
        }
    }

    async function ingestDocument(index: number): Promise<boolean> {
        const doc = documents.value[index]
        if (!doc) return false

        const file = doc.file
        const name = file.name.toLowerCase()

        // Support PDF, TXT, and MD files
        if (!name.endsWith('.txt') && !name.endsWith('.md') && !name.endsWith('.pdf')) {
            updateDocumentStatus(index, 'error', { error: 'Only PDF, TXT, and MD files can be ingested' })
            return false
        }

        try {
            updateDocumentStatus(index, 'ingesting')

            // Ensure we have a session before ingesting
            const currentSessionId = await ensureSession()

            // Use FormData for file upload (required for PDF parsing on backend)
            const formData = new FormData()
            formData.append('file', file)

            // Send file to session-based backend endpoint
            const response = await $fetch<{ chunks_ingested: number }>(
                `/api/sessions/${currentSessionId}/ingest`,
                {
                    method: 'POST',
                    body: formData
                }
            )

            updateDocumentStatus(index, 'ingested', { chunksIngested: response.chunks_ingested })
            return true
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to ingest document'
            updateDocumentStatus(index, 'error', { error: errorMessage })
            return false
        }
    }

    function clearPrompt() {
        currentPrompt.value = ''
    }

    function getDocumentMetadata() {
        return documents.value.map(d => ({
            name: d.file.name,
            type: d.file.type,
            size: d.file.size,
            status: d.status
        }))
    }

    // Flashcard methods
    function setFlashcards(cards: Flashcard[]) {
        flashcards.value = cards
    }

    function openFlashcardPanel() {
        isFlashcardPanelOpen.value = true
    }

    function closeFlashcardPanel() {
        isFlashcardPanelOpen.value = false
    }

    async function generateFlashcards(): Promise<void> {
        if (isGeneratingFlashcards.value) return
        if (!sessionId.value) {
            console.error('No session available for flashcard generation')
            return
        }

        isGeneratingFlashcards.value = true
        openFlashcardPanel()

        try {
            const response = await $fetch<{ flashcards: Flashcard[] }>('/api/flashcards', {
                method: 'POST',
                body: {
                    sessionId: sessionId.value,
                    topic: 'content from uploaded documents',
                    count: 10
                }
            })

            setFlashcards(response.flashcards)
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to generate flashcards'
            console.error('Flashcard generation error:', errorMessage)
            setFlashcards([])
        } finally {
            isGeneratingFlashcards.value = false
        }
    }

    return {
        messages,
        currentPrompt,
        documents,
        sessionId,
        hasIngestedDocuments,
        addMessage,
        addDocument,
        removeDocument,
        updateDocumentStatus,
        ingestDocument,
        ensureSession,
        clearPrompt,
        getDocumentMetadata,
        // Flashcard exports
        flashcards,
        isFlashcardPanelOpen,
        isGeneratingFlashcards,
        setFlashcards,
        openFlashcardPanel,
        closeFlashcardPanel,
        generateFlashcards
    }
}
