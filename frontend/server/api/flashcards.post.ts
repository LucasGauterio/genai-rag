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

interface BackendFlashcard {
    question: string
    answer: string
    citation?: string
}

interface BackendCitation {
    citation_id: string
    source: string
    page: number
    text: string
    start_offset: number
    end_offset: number
}

interface BackendFlashcardsResponse {
    flashcards: BackendFlashcard[]
    citations: Record<string, BackendCitation>
    topic?: string
}

/**
 * Parse and transform the backend flashcards response into frontend format.
 * Adds unique IDs to each flashcard.
 */
function parseFlashcardsResponse(backendResponse: BackendFlashcardsResponse): {
    flashcards: Flashcard[]
    citations: CitationsMap
} {
    const flashcards = backendResponse.flashcards.map((card, index) => ({
        id: String(index + 1),
        question: card.question,
        answer: card.answer,
        citation: card.citation
    }))

    // Transform citations to frontend format
    const citations: CitationsMap = {}
    for (const [key, value] of Object.entries(backendResponse.citations || {})) {
        citations[key] = {
            citation_id: value.citation_id,
            source: value.source,
            page: value.page,
            text: value.text,
            start_offset: value.start_offset,
            end_offset: value.end_offset
        }
    }

    return { flashcards, citations }
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

        const parsed = parseFlashcardsResponse(backendResponse)

        return {
            flashcards: parsed.flashcards,
            citations: parsed.citations
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
