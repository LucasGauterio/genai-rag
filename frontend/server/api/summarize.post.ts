export default defineEventHandler(async (event) => {
    const body = await readBody(event)

    // Mock response - no real backend logic
    const { prompt, documents } = body

    // Simulate slight delay like a real API
    await new Promise(resolve => setTimeout(resolve, 500))

    const docCount = documents?.length || 0
    const response = docCount > 0
        ? `This is a mock response based on your ${docCount} document(s). You asked: "${prompt}"`
        : `This is a mock response. You asked: "${prompt}" (No documents uploaded yet)`

    return {
        response
    }
})
