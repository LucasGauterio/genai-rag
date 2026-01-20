#!/usr/bin/env python3
"""
Flashcard Generator - CLI Interface

Command-line tool for generating flashcards from technical documents.

Usage:
    python main.py ingest --input /path/to/documents
    python main.py generate --topic "Machine Learning"
    python main.py generate --input docs/notes.pdf --output flashcards.json
"""

import json
import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

# Local imports
from config import CHROMA_PATH, OUTPUT_DIR
from chunking import load_and_chunk_document, load_and_chunk_directory
from retrieval import VectorStore, HybridRetriever, create_hybrid_retriever
from retrieval.hybrid_retriever import format_retrieved_docs
from generation import (
    ExtractorChain,
    TransformationChain,
    validate_flashcards,
    FlashcardSet,
)
from validation import validate_and_correct_cards

console = Console()


@click.group()
def cli():
    """Flashcard Generator - Create exam-ready flashcards from technical documents."""
    pass


@cli.command()
@click.option(
    '--input', '-i', 'input_path',
    required=True,
    type=click.Path(exists=True),
    help='Path to document file or directory'
)
@click.option(
    '--clear/--no-clear',
    default=True,
    help='Clear existing database before ingesting'
)
def ingest(input_path: str, clear: bool):
    """Ingest documents into the vector store."""
    
    input_path = Path(input_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: Load and chunk documents
        task = progress.add_task("Loading and chunking documents...", total=None)
        
        if input_path.is_dir():
            chunks = load_and_chunk_directory(input_path)
        else:
            chunks = load_and_chunk_document(input_path)
        
        progress.update(task, description=f"Loaded {len(chunks)} chunks")
        
        # Step 2: Create vector store
        progress.update(task, description="Creating vector store...")
        
        vector_store = VectorStore()
        vector_store.create_from_documents(chunks, clear_existing=clear)
        
        progress.update(task, description="Done!")
    
    console.print(Panel(
        f"[green]✓ Ingested {len(chunks)} chunks into vector store[/green]\n"
        f"  Database: {CHROMA_PATH}",
        title="Ingestion Complete"
    ))


@cli.command()
@click.option(
    '--input', '-i', 'input_path',
    type=click.Path(exists=True),
    help='Path to document (ingests and generates in one step)'
)
@click.option(
    '--topic', '-t',
    help='Topic/query to focus flashcard generation on'
)
@click.option(
    '--output', '-o', 'output_path',
    default='flashcards.json',
    help='Output file path for generated flashcards'
)
@click.option(
    '--max-cards', '-n',
    default=20,
    type=int,
    help='Maximum number of flashcards to generate'
)
@click.option(
    '--validate/--no-validate',
    default=True,
    help='Run self-correction validation on generated cards'
)
@click.option(
    '--doc-ids',
    multiple=True,
    help='Filter by specific document IDs'
)
def generate(
    input_path: str,
    topic: str,
    output_path: str,
    max_cards: int,
    validate: bool,
    doc_ids: tuple,
):
    """Generate flashcards from documents."""
    
    vector_store = VectorStore()
    
    # If input provided, ingest first
    if input_path:
        input_path = Path(input_path)
        
        with console.status("Ingesting document..."):
            if input_path.is_dir():
                chunks = load_and_chunk_directory(input_path)
            else:
                chunks = load_and_chunk_document(input_path)
            
            vector_store.create_from_documents(chunks, clear_existing=True)
            console.print(f"[green]✓ Ingested {len(chunks)} chunks[/green]")
    
    # Check if we have documents
    if vector_store.count == 0:
        console.print("[red]Error: No documents in vector store. Run 'ingest' first or provide --input[/red]")
        return
    
    # Default topic if not provided
    if not topic:
        topic = "Generate comprehensive flashcards covering all key concepts"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Step 1: Retrieve relevant chunks
        task = progress.add_task("Retrieving relevant content...", total=None)
        
        retriever = create_hybrid_retriever(vector_store)
        doc_id_list = list(doc_ids) if doc_ids else None
        retrieved_docs = retriever.retrieve(topic, doc_ids=doc_id_list)
        
        if not retrieved_docs:
            console.print("[red]No relevant content found for the topic.[/red]")
            return
        
        source_context = format_retrieved_docs(retrieved_docs)
        progress.update(task, description=f"Retrieved {len(retrieved_docs)} chunks")
        
        # Step 2: Extract concepts
        progress.update(task, description="Extracting key concepts...")
        
        extractor = ExtractorChain()
        extracted = extractor.extract(source_context)
        
        # Step 3: Transform to flashcards
        progress.update(task, description="Generating flashcards...")
        
        transformer = TransformationChain()
        # Returns a FlashcardSet directly, no need for string parsing
        card_set = transformer.transform(extracted)
        
        # Step 4: (Skipped) Transformation now handles structured output directly
        # card_set is already a validated FlashcardSet object
        
        # Step 5: Self-correction (optional)
        stats = None
        if validate:
            progress.update(task, description="Running self-correction...")
            card_set, stats = validate_and_correct_cards(card_set, source_context)
        
        # Limit to max_cards
        if len(card_set.cards) > max_cards:
            card_set = FlashcardSet(cards=card_set.cards[:max_cards])
        
        progress.update(task, description="Done!")
    
    # Save output
    output_file = Path(output_path)
    if not output_file.is_absolute():
        output_file = OUTPUT_DIR / output_file
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(card_set.to_dict(), f, indent=2)
    
    # Display results
    _display_results(card_set, stats, output_file)


def _display_results(card_set: FlashcardSet, stats: dict, output_file: Path):
    """Display generation results in a nice table."""
    
    console.print()
    console.print(Panel(
        f"[green]✓ Generated {len(card_set.cards)} flashcards[/green]\n"
        f"  Output: {output_file}",
        title="Generation Complete"
    ))
    
    if stats:
        stats_table = Table(title="Validation Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total Cards", str(stats.get("total", 0)))
        stats_table.add_row("Accepted", str(stats.get("accepted", 0)))

        stats_table.add_row("Rejected", str(stats.get("rejected", 0)))
        stats_table.add_row("Avg Accuracy", f"{stats.get('avg_accuracy', 0):.2f}/5")
        stats_table.add_row("Avg Overall", f"{stats.get('avg_overall', 0):.2f}/5")
        
        console.print(stats_table)
    
    # Show sample cards
    console.print("\n[bold]Sample Flashcards:[/bold]\n")
    
    for i, card in enumerate(card_set.cards[:3], 1):
        console.print(f"[cyan]Card {i}[/cyan] [{card.tag}]")
        console.print(f"  Q: {card.question}")
        console.print(f"  A: {card.answer[:100]}..." if len(card.answer) > 100 else f"  A: {card.answer}")
        console.print()


@cli.command()
def status():
    """Show vector store status."""
    
    vector_store = VectorStore()
    count = vector_store.count
    
    if count > 0:
        console.print(f"[green]Vector store contains {count} documents[/green]")
        console.print(f"  Location: {CHROMA_PATH}")
    else:
        console.print("[yellow]Vector store is empty. Run 'ingest' to add documents.[/yellow]")


@cli.command()
def clear():
    """Clear the vector store."""
    
    if click.confirm("This will delete all indexed documents. Continue?"):
        vector_store = VectorStore()
        vector_store.clear()
        console.print("[green]Vector store cleared.[/green]")


if __name__ == "__main__":
    cli()
