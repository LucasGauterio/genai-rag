export interface Flashcard {
    id: string
    question: string
    answer: string
}

// Mock flashcards for development - will be replaced with real backend response
const mockFlashcards: Flashcard[] = [
    {
        id: '1',
        question: 'What is Retrieval-Augmented Generation (RAG)?',
        answer: 'RAG is an AI framework that combines information retrieval with text generation. It retrieves relevant documents from a knowledge base and uses them as context for generating more accurate and grounded responses.'
    },
    {
        id: '2',
        question: 'What are vector embeddings?',
        answer: 'Vector embeddings are numerical representations of text that capture semantic meaning. Similar texts have similar vector representations, enabling semantic search and similarity matching.'
    },
    {
        id: '3',
        question: 'What is a chunk in document processing?',
        answer: 'A chunk is a smaller segment of a larger document, typically split by character count, sentences, or semantic boundaries. Chunking improves retrieval accuracy by allowing more precise matching.'
    },
    {
        id: '4',
        question: 'What is the purpose of a vector database?',
        answer: 'A vector database stores and indexes vector embeddings, enabling fast similarity searches. It allows finding semantically similar content without exact keyword matching.'
    },
    {
        id: '5',
        question: 'What is semantic search?',
        answer: 'Semantic search finds results based on meaning rather than exact keywords. It uses vector embeddings to match queries with content that has similar semantic meaning.'
    },
    {
        id: '6',
        question: 'What is the difference between RAG and fine-tuning?',
        answer: 'RAG retrieves external knowledge at query time without modifying the model, while fine-tuning permanently adjusts model weights with new data. RAG is more flexible and easier to update.'
    },
    {
        id: '7',
        question: 'What is context window in LLMs?',
        answer: 'The context window is the maximum amount of text (measured in tokens) that an LLM can process in a single request. It limits how much retrieved content can be included in RAG prompts.'
    }
]

/**
 * Parse the backend response into flashcard format.
 * Currently returns mock data; will parse real response when backend is ready.
 */
function parseFlashcardsResponse(_backendResponse: unknown): Flashcard[] {
    // TODO: Parse actual backend response format when available
    // Expected format from Flask backend:
    // { flashcards: [{ question: string, answer: string }, ...] }
    return mockFlashcards
}

export default defineEventHandler(async (event) => {
    const body = await readBody(event)

    try {
        // Simulate network delay for realistic UX
        await new Promise(resolve => setTimeout(resolve, 1000))

        // TODO: Call Flask backend when endpoint is ready
        // const backendResponse = await $fetch('http://localhost:5000/api/flashcards', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: { documents: body.documents }
        // })

        return {
            flashcards: parseFlashcardsResponse(null)
        }
    } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error'

        throw createError({
            statusCode: 503,
            statusMessage: `Backend unavailable: ${errorMessage}`
        })
    }
})
