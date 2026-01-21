import type { Ref } from 'vue'

export interface Message {
    role: 'user' | 'assistant'
    content: string
    citations?: CitationsMap
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

export interface Citation {
    citation_id: string
    source: string
    page: number
    text: string
    start_offset: number
    end_offset: number
}

export type CitationsMap = Record<string, Citation>

export const FLASHCARD_COUNT_MIN = 3
export const FLASHCARD_COUNT_MAX = 10

let documentsState: Ref<Document[]> | null = null

function getDocumentsRef(): Ref<Document[]> {
    if (!documentsState) {
        documentsState = ref<Document[]>([])
    }
    return documentsState
}

export function useAppState() {
    const messages = useState<Message[]>('messages', () => [])
    const currentPrompt = useState<string>('currentPrompt', () => '')
    const sessionId = useState<string | null>('sessionId', () => null)
    const sessionLoadState = useState<'idle' | 'loading' | 'error'>('sessionLoadState', () => 'idle')
    const flashcards = useState<Flashcard[]>('flashcards', () => [])
    const citations = useState<CitationsMap>('citations', () => ({}))
    const isFlashcardPanelOpen = useState<boolean>('isFlashcardPanelOpen', () => false)
    const isGeneratingFlashcards = useState<boolean>('isGeneratingFlashcards', () => false)
    const flashcardCount = useState<number>('flashcardCount', () => 10)

    const documents = getDocumentsRef()

    const hasIngestedDocuments = computed(() =>
        documents.value.some(d => d.status === 'ingested')
    )

    async function ensureSession(): Promise<string> {
        if (sessionId.value) return sessionId.value

        const response = await $fetch<{ session_id: string }>('/api/sessions', { method: 'POST' })
        sessionId.value = response.session_id
        return response.session_id
    }

    function addMessage(role: 'user' | 'assistant', content: string, messageCitations?: CitationsMap) {
        messages.value.push({ role, content, citations: messageCitations })
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

        const name = doc.file.name.toLowerCase()
        if (!name.endsWith('.txt') && !name.endsWith('.md') && !name.endsWith('.pdf')) {
            updateDocumentStatus(index, 'error', { error: 'Only PDF, TXT, and MD files can be ingested' })
            return false
        }

        try {
            updateDocumentStatus(index, 'ingesting')
            const currentSessionId = await ensureSession()

            const formData = new FormData()
            formData.append('file', doc.file)

            const response = await $fetch<{ chunks_ingested: number }>(
                `/api/sessions/${currentSessionId}/ingest`,
                { method: 'POST', body: formData }
            )

            updateDocumentStatus(index, 'ingested', { chunksIngested: response.chunks_ingested })
            return true
        } catch (err: unknown) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to ingest document'
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

    function setFlashcards(cards: Flashcard[]) {
        flashcards.value = cards
    }

    function setCitations(citationData: CitationsMap) {
        citations.value = citationData
    }

    function openFlashcardPanel() {
        isFlashcardPanelOpen.value = true
    }

    function closeFlashcardPanel() {
        isFlashcardPanelOpen.value = false
    }

    async function generateFlashcards(): Promise<void> {
        if (isGeneratingFlashcards.value || !sessionId.value) return

        isGeneratingFlashcards.value = true
        openFlashcardPanel()

        try {
            const response = await $fetch<{ flashcards: Flashcard[]; citations: CitationsMap }>('/api/flashcards', {
                method: 'POST',
                body: {
                    sessionId: sessionId.value,
                    topic: 'content from uploaded documents',
                    count: flashcardCount.value
                }
            })

            setFlashcards(response.flashcards)
            setCitations(response.citations || {})
        } catch (err: unknown) {
            console.error('Flashcard generation error:', err instanceof Error ? err.message : err)
            setFlashcards([])
            setCitations({})
        } finally {
            isGeneratingFlashcards.value = false
        }
    }

    return {
        messages,
        currentPrompt,
        documents,
        sessionId,
        sessionLoadState,
        hasIngestedDocuments,
        addMessage,
        addDocument,
        removeDocument,
        updateDocumentStatus,
        ingestDocument,
        ensureSession,
        clearPrompt,
        getDocumentMetadata,
        flashcards,
        citations,
        flashcardCount,
        isFlashcardPanelOpen,
        isGeneratingFlashcards,
        setFlashcards,
        setCitations,
        openFlashcardPanel,
        closeFlashcardPanel,
        generateFlashcards
    }
}
