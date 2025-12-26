import { ref } from 'vue'

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

// Shared state - in-memory only, clears on reload
const messages = ref<Message[]>([])
const currentPrompt = ref('')
const documents = ref<Document[]>([])

export function useAppState() {
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

            // Use FormData for file upload (required for PDF parsing on backend)
            const formData = new FormData()
            formData.append('file', file)

            // Send file to backend for processing
            const response = await $fetch<{ chunks_ingested: number }>('/api/ingest-file', {
                method: 'POST',
                body: formData
            })

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

    return {
        messages,
        currentPrompt,
        documents,
        addMessage,
        addDocument,
        removeDocument,
        updateDocumentStatus,
        ingestDocument,
        clearPrompt,
        getDocumentMetadata
    }
}
