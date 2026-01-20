"""
Flashcard Generator - Streamlit UI

A modern web interface for generating flashcards from technical documents.

Run with: streamlit run app.py
"""

import json
import streamlit as st
from pathlib import Path
import tempfile

# Local imports
from config import OUTPUT_DIR
from chunking import load_and_chunk_document
from retrieval import VectorStore, create_hybrid_retriever
from retrieval.hybrid_retriever import format_retrieved_docs
from generation import ExtractorChain, TransformationChain, validate_flashcards, FlashcardSet
from validation import validate_and_correct_cards


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Flashcard Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    .flashcard {
        background: linear-gradient(145deg, #1e3a5f 0%, #0d2137 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid #4ecdc4;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .flashcard-question {
        color: #4ecdc4;
        font-size: 1.1em;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .flashcard-answer {
        color: #e8e8e8;
        font-size: 1em;
        line-height: 1.6;
    }
    .flashcard-tag {
        display: inline-block;
        background: rgba(78, 205, 196, 0.2);
        color: #4ecdc4;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8em;
        margin-top: 10px;
    }
    .stat-card {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .stat-value {
        font-size: 2em;
        font-weight: bold;
        color: #4ecdc4;
    }
    .stat-label {
        color: #888;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE
# =============================================================================

if 'flashcards' not in st.session_state:
    st.session_state.flashcards = None
if 'generation_stats' not in st.session_state:
    st.session_state.generation_stats = None
if 'source_context' not in st.session_state:
    st.session_state.source_context = None


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.title("📚 Flashcard Generator")
    st.markdown("---")
    
    st.subheader("📄 Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'md', 'txt'],
        help="Upload PDF, Markdown, or Text files"
    )
    
    st.markdown("---")
    
    st.subheader("⚙️ Generation Settings")
    
    topic = st.text_input(
        "Topic/Focus",
        value="Generate flashcards for all key concepts",
        help="Specify what topics to focus on"
    )
    
    max_cards = st.slider(
        "Max Cards",
        min_value=5,
        max_value=50,
        value=20,
        help="Maximum number of flashcards to generate"
    )
    
    enable_validation = st.checkbox(
        "Enable Self-Correction",
        value=True,
        help="Run LLM validation to ensure accuracy"
    )
    
    st.markdown("---")
    
    # Process button
    generate_button = st.button(
        "🚀 Generate Flashcards",
        type="primary",
        disabled=uploaded_file is None,
        use_container_width=True,
    )


# =============================================================================
# MAIN CONTENT
# =============================================================================

st.title("📚 AI Flashcard Generator")
st.markdown("Transform your technical documents into exam-ready flashcards using advanced RAG and multi-step generation.")

# Generation flow
if generate_button and uploaded_file:
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    
    try:
        # Progress container
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0, text="Starting...")
            
            # Step 1: Ingest document
            progress_bar.progress(10, text="📥 Parsing document...")
            
            chunks = load_and_chunk_document(tmp_path)
            
            # Step 2: Create vector store
            progress_bar.progress(25, text="🔍 Creating vector index...")
            
            vector_store = VectorStore()
            vector_store.create_from_documents(chunks, clear_existing=True)
            
            # Step 3: Retrieve relevant content
            progress_bar.progress(40, text="🎯 Retrieving relevant content...")
            
            retriever = create_hybrid_retriever(vector_store)
            retrieved_docs = retriever.retrieve(topic)
            source_context = format_retrieved_docs(retrieved_docs)
            st.session_state.source_context = source_context
            
            # Step 4: Extract concepts
            progress_bar.progress(55, text="🧠 Extracting key concepts...")
            
            extractor = ExtractorChain()
            extracted = extractor.extract(source_context)
            
            # Step 5: Transform to flashcards
            progress_bar.progress(70, text="✨ Generating flashcards...")
            
            transformer = TransformationChain()
            raw_cards = transformer.transform(extracted)
            
            # Step 6: Validate structure
            progress_bar.progress(80, text="✓ Validating output...")
            
            card_set = validate_flashcards(raw_cards)
            
            # Step 7: Self-correction
            stats = None
            if enable_validation:
                progress_bar.progress(90, text="🔄 Running self-correction...")
                card_set, stats = validate_and_correct_cards(card_set, source_context)
                st.session_state.generation_stats = stats
            
            # Limit cards
            if len(card_set.cards) > max_cards:
                card_set = FlashcardSet(cards=card_set.cards[:max_cards])
            
            st.session_state.flashcards = card_set
            
            progress_bar.progress(100, text="✅ Complete!")
        
        st.success(f"Generated {len(card_set.cards)} flashcards!")
        
    except Exception as e:
        st.error(f"Error during generation: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)


# Display results
if st.session_state.flashcards:
    
    st.markdown("---")
    
    # Statistics
    if st.session_state.generation_stats:
        stats = st.session_state.generation_stats
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Cards", len(st.session_state.flashcards.cards))
        with col2:
            st.metric("Accepted", stats.get("accepted", 0))
        with col3:
            st.metric("Revised", stats.get("revised", 0))
        with col4:
            st.metric("Avg Score", f"{stats.get('avg_overall', 0):.1f}/5")
    
    st.markdown("---")
    
    # Flashcard display
    st.subheader("📇 Generated Flashcards")
    
    # Filter by tag
    all_tags = list(set(card.tag for card in st.session_state.flashcards.cards))
    selected_tags = st.multiselect(
        "Filter by tag",
        options=all_tags,
        default=all_tags,
    )
    
    # Display cards
    filtered_cards = [c for c in st.session_state.flashcards.cards if c.tag in selected_tags]
    
    for i, card in enumerate(filtered_cards, 1):
        with st.expander(f"Card {i}: {card.question[:60]}...", expanded=i <= 3):
            st.markdown(f"**Question:** {card.question}")
            st.markdown(f"**Answer:** {card.answer}")
            st.markdown(f"**Tag:** `{card.tag}`")
    
    st.markdown("---")
    
    # Export options
    st.subheader("📥 Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        json_data = st.session_state.flashcards.to_json()
        st.download_button(
            "📄 Download JSON",
            data=json_data,
            file_name="flashcards.json",
            mime="application/json",
            use_container_width=True,
        )
    
    with col2:
        # CSV export
        import csv
        import io
        
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["Question", "Answer", "Tag"])
        for card in st.session_state.flashcards.cards:
            writer.writerow([card.question, card.answer, card.tag])
        
        st.download_button(
            "📊 Download CSV",
            data=csv_buffer.getvalue(),
            file_name="flashcards.csv",
            mime="text/csv",
            use_container_width=True,
        )

else:
    # Welcome message when no flashcards generated yet
    st.markdown("""
    ### 🚀 Getting Started
    
    1. **Upload** a document (PDF, Markdown, or Text) in the sidebar
    2. **Configure** your generation settings
    3. **Click** "Generate Flashcards" to start
    
    The system will:
    - Parse your document with structure awareness
    - Use hybrid search (semantic + keyword) to find relevant content
    - Extract key concepts in a multi-step flow
    - Generate Q&A pairs with strict JSON schema
    - Validate accuracy against source material
    """)
    
    # Sample output
    st.markdown("### 📋 Sample Output Format")
    st.code('''
{
  "cards": [
    {
      "question": "What is gradient descent?",
      "answer": "An optimization algorithm that iteratively adjusts parameters to minimize a loss function by following the negative gradient.",
      "tag": "definition"
    },
    {
      "question": "What is the difference between batch and stochastic gradient descent?",
      "answer": "Batch GD computes gradients over the entire dataset, while SGD uses a single sample per update, trading accuracy for speed.",
      "tag": "comparison"
    }
  ]
}
    ''', language='json')
