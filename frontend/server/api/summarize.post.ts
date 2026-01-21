export default defineEventHandler(async (event) => {
    const config = useRuntimeConfig()
    const { prompt, sessionId } = await readBody(event)

    if (!sessionId) {
        throw createError({ statusCode: 400, statusMessage: 'Missing sessionId' })
    }
    if (!prompt) {
        throw createError({ statusCode: 400, statusMessage: 'Missing prompt' })
    }

    try {
        const response = await $fetch<{
            answer: string
            citations: Record<string, unknown>
            chunks_used?: number
        }>(`${config.backendApiUrl}/api/sessions/${sessionId}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: { question: prompt, mode: 'chat', k: 5 }
        })

        return {
            response: response.answer,
            citations: response.citations,
            chunksUsed: response.chunks_used
        }
    } catch (err: unknown) {
        if (typeof err === 'object' && err !== null && 'data' in err) {
            const fetchError = err as { data?: { error?: string } }
            if (fetchError.data?.error) {
                throw createError({ statusCode: 400, statusMessage: fetchError.data.error })
            }
        }

        const msg = err instanceof Error ? err.message : 'Unknown error'
        throw createError({ statusCode: 503, statusMessage: `Backend unavailable: ${msg}` })
    }
})
