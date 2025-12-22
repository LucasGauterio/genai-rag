## Test /ingest
curl -X POST http://127.0.0.1:5000/api/ingest \
     -H "Content-Type: application/json" \
     -d '{"text": "Flask is a lightweight Python framework for web apps."}'

Response:
{
  "chunks_ingested": 1
}


## Test /chat
curl -X POST http://127.0.0.1:5000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"question": "What is Flask?"}'
     
Response:
{
  "answer": "Flask is a lightweight Python web framework.",
  "context": "Flask is a lightweight Python framework for web apps."
}
