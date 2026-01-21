export default defineEventHandler(async (event) => {
    const config = useRuntimeConfig()
    const body = await readBody(event)
    const { prompt, sessionId } = body

    if (!sessionId) {
        throw createError({
            statusCode: 400,
            statusMessage: 'Missing sessionId'
        })
    }

    if (!prompt) {
        throw createError({
            statusCode: 400,
            statusMessage: 'Missing prompt'
        })
    }

    try {
        // Forward request to Flask backend session-based chat endpoint
        const backendResponse = await $fetch<{
            answer: string
            citations: Record<string, unknown>
            chunks_used?: number
        }>(`${config.backendApiUrl}/api/sessions/${sessionId}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: {
                question: prompt,
                mode: 'chat',
                k: 5
            }
        })

        return {
            response: backendResponse.answer,
            citations: backendResponse.citations,
            chunksUsed: backendResponse.chunks_used
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
