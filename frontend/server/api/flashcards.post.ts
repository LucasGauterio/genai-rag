export interface Flashcard {
    id: string
    question: string
    answer: string
    citation?: string
}

interface BackendFlashcard {
    question: string
    answer: string
    citation?: string
}

interface BackendFlashcardsResponse {
    flashcards: BackendFlashcard[]
    citations: Record<string, unknown>
    topic?: string
}

/**
 * Parse and transform the backend flashcards response into frontend format.
 * Adds unique IDs to each flashcard.
 */
function parseFlashcardsResponse(backendResponse: BackendFlashcardsResponse): Flashcard[] {
    return backendResponse.flashcards.map((card, index) => ({
        id: String(index + 1),
        question: card.question,
        answer: card.answer,
        citation: card.citation
    }))
}

export default defineEventHandler(async (event) => {
    const body = await readBody(event)
    const { sessionId, topic, count } = body

    if (!sessionId) {
        throw createError({
            statusCode: 400,
            statusMessage: 'Missing sessionId'
        })
    }

    if (!topic) {
        throw createError({
            statusCode: 400,
            statusMessage: 'Missing topic'
        })
    }

    try {
        // Call Flask backend session-based flashcard endpoint
        const backendResponse = await $fetch<BackendFlashcardsResponse>(
            `http://localhost:5000/api/sessions/${sessionId}/flashcards`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: {
                    topic,
                    count: count || 10
                }
            }
        )

        return {
            flashcards: parseFlashcardsResponse(backendResponse)
        }
    } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error'

        // Check if it's a fetch error with response details
        if (typeof error === 'object' && error !== null && 'data' in error) {
            const fetchError = error as { data?: { error?: string } }
            if (fetchError.data?.error) {
                throw createError({
                    statusCode: 400,
                    statusMessage: fetchError.data.error
                })
            }
        }

        throw createError({
            statusCode: 503,
            statusMessage: `Backend unavailable: ${errorMessage}`
        })
    }
})
