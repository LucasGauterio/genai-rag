export default defineEventHandler(async (event) => {
    const body = await readBody(event)
    const { prompt } = body

    try {
        // Forward request to Flask backend
        const backendResponse = await $fetch<{ answer: string; context: string[] }>('http://localhost:5000/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: {
                question: prompt // Map frontend's 'prompt' to backend's 'question'
            }
        })

        return {
            response: backendResponse.answer,
            context: backendResponse.context
        }
    } catch (error: unknown) {
        // Handle network or backend errors
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
