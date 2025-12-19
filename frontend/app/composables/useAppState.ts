import { ref } from 'vue'

interface Message {
    role: 'user' | 'assistant'
    content: string
}

// Shared state - in-memory only, clears on reload
const messages = ref<Message[]>([])
const currentPrompt = ref('')
const documents = ref<File[]>([])

export function useAppState() {
    function addMessage(role: 'user' | 'assistant', content: string) {
        messages.value.push({ role, content })
    }

    function addDocument(file: File) {
        documents.value.push(file)
    }

    function removeDocument(index: number) {
        documents.value.splice(index, 1)
    }

    function clearPrompt() {
        currentPrompt.value = ''
    }

    function getDocumentMetadata() {
        return documents.value.map(f => ({
            name: f.name,
            type: f.type,
            size: f.size
        }))
    }

    return {
        messages,
        currentPrompt,
        documents,
        addMessage,
        addDocument,
        removeDocument,
        clearPrompt,
        getDocumentMetadata
    }
}
