"""Test script to check semantic similarity scores."""

import sys
sys.path.insert(0, '/Volumes/WorkSpace/Projects/InterviewPreps/ThoughfulAI')

from src.services.vector_store import vector_store_service
from src.config import settings

# Initialize vector store
print("Initializing vector store...")
vector_store_service.initialize()
print(f"Loaded {vector_store_service.get_document_count()} documents\n")

# Test queries
test_queries = [
    "Tell me about Thoughtful AI's Agents.",  # Exact match from dataset
    "What is Thoughtful AI's Agents?",        # Paraphrased
    "What are Thoughtful AI's Agents?",       # Paraphrased
    "Describe Thoughtful AI's Agents",        # Paraphrased
    "Tell me about the agents",               # Shorter version
    "What does EVA do?",                      # Different question
    "How does CAM work?",                     # Different question
    "What is machine learning?",              # Unrelated
]

print("=" * 80)
print("SEMANTIC SIMILARITY TEST")
print("=" * 80)
print(f"Similarity Threshold: {settings.similarity_threshold}")
print("=" * 80)

for query in test_queries:
    print(f"\nQuery: '{query}'")
    print("-" * 80)
    
    # Get results with scores
    results = vector_store_service.similarity_search_with_score(query, k=3)
    
    if results:
        for i, (doc, distance) in enumerate(results, 1):
            # Convert distance to similarity (same formula as RAG agent)
            similarity = max(0, 1 - (distance / 2))
            
            # Extract question from document
            question = doc.metadata.get('question', 'N/A')
            
            # Determine if it would match
            match_status = "✅ EXACT MATCH" if similarity >= settings.similarity_threshold else "❌ LLM FALLBACK"
            
            print(f"  [{i}] Distance: {distance:.4f} | Similarity: {similarity:.4f} | {match_status}")
            print(f"      Matched Question: '{question}'")
    else:
        print("  No results found!")

print("\n" + "=" * 80)
print("ANALYSIS:")
print("=" * 80)
print(f"- Threshold: {settings.similarity_threshold}")
print("- Queries with similarity >= threshold will return exact answers")
print("- Queries with similarity < threshold will use LLM generation")
print("=" * 80)
