"""
Axoora RAG (Retrieval-Augmented Generation) Engine.
Combines semantic vector embeddings and lexical indexing to retrieve verified
banking knowledge documents and generate accurate, grounded customer answers.
"""

from __future__ import annotations

import os
import re
import math
import json
import logging
from typing import Optional, List, Dict, Any
import requests
from django.conf import settings
from .models import KnowledgeChunk, KnowledgeDocument

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
    'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
    'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
    'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
    'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
    'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
    'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
    'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
    'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
}


def tokenize(text: str) -> list[str]:
    """Tokenize and filter stop words."""
    words = re.findall(r'\b[a-zA-Z0-9_\-\.]{2,}\b', text.lower())
    return [w for w in words if w not in STOP_WORDS]


def get_embedding(text: str) -> list[float] | None:
    """
    Generate vector embeddings using Gemini or OpenAI if API keys are configured.
    Falls back gracefully if offline.
    """
    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
            payload = {
                "model": "models/text-embedding-004",
                "content": {"parts": [{"text": text[:2000]}]}
            }
            resp = requests.post(url, json=payload, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("embedding", {}).get("values")
        except Exception as e:
            logger.debug(f"Gemini embedding error: {e}")

    if OPENAI_API_KEY:
        try:
            url = "https://api.openai.com/v1/embeddings"
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "text-embedding-3-small", "input": text[:2000]}
            resp = requests.post(url, headers=headers, json=payload, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            logger.debug(f"OpenAI embedding error: {e}")

    return None


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def calculate_lexical_score(query_tokens: list[str], chunk_title: str, chunk_content: str, keywords: str) -> float:
    """Calculate lexical relevance score for the chunk."""
    if not query_tokens:
        return 0.0

    content_lower = chunk_content.lower()
    title_lower = chunk_title.lower()
    kw_lower = keywords.lower()

    score = 0.0
    total_tokens = len(query_tokens)

    for token in query_tokens:
        term_score = 0.0
        # Title match has high weight
        if token in title_lower:
            term_score += 2.0
        # Keywords tag match
        if token in kw_lower:
            term_score += 1.5
        # Exact content occurrences
        count = content_lower.count(token)
        if count > 0:
            term_score += min(count * 0.5, 2.0)

        score += term_score

    # Normalized score
    return min(score / (total_tokens * 2.0), 1.0)


def retrieve_relevant_chunks(query: str, top_k: int = 3) -> list[dict]:
    """
    RAG Retrieval Phase:
    Retrieves the top-k most relevant knowledge items across KnowledgeChunk,
    live FaqItem, and live ProductItem records so admin CMS edits immediately
    reflect in AI Concierge answers.
    """
    from ..content.models import FaqItem, ProductItem

    query_tokens = tokenize(query)
    query_embedding = get_embedding(query)

    chunks = KnowledgeChunk.get_all_chunks()
    scored_results: list[dict] = []

    for chunk in chunks:
        lexical = calculate_lexical_score(query_tokens, chunk.chunk_title, chunk.content, chunk.keywords)

        if query_embedding and chunk.embedding:
            semantic = cosine_similarity(query_embedding, chunk.embedding)
            combined_score = (0.6 * semantic) + (0.4 * lexical)
        else:
            combined_score = lexical

        if combined_score > 0.12:
            scored_results.append({
                'id': str(chunk.id),
                'title': chunk.chunk_title,
                'content': chunk.content,
                'source_type': chunk.source_type,
                'document_title': chunk.document.title if chunk.document else chunk.chunk_title,
                'document_category': chunk.document.category if chunk.document else 'general',
                'score': combined_score,
            })

    # Also score live ProductItem records from the CMS catalog (1 query)
    for product in ProductItem.get_all():
        prod_text = (
            f"{product.name} ({product.category}): {product.headline}. "
            f"Fee structure: {product.fee_structure}. {product.highlight}. {product.description}"
        )
        lexical = calculate_lexical_score(
            query_tokens,
            product.name,
            prod_text,
            f"{product.category} {product.fee_structure} {product.highlight} pos fee account",
        )
        if lexical > 0.12:
            scored_results.append({
                'id': str(product.id),
                'title': product.name,
                'content': prod_text,
                'source_type': 'product',
                'document_title': f"Axoora Product Suite — {product.name}",
                'document_category': 'pos' if product.category == 'hardware' else product.category,
                'score': lexical + 0.05,  # Prefer live catalog specs on exact matches
            })

    # Also score live FaqItem records from the CMS FAQ table (1 query)
    for faq in FaqItem.get_active_faqs():
        lexical = calculate_lexical_score(
            query_tokens,
            faq.question,
            f"{faq.question} {faq.answer}",
            f"{faq.category} faq",
        )
        if lexical > 0.12:
            scored_results.append({
                'id': str(faq.id),
                'title': faq.question,
                'content': faq.answer,
                'source_type': 'faq',
                'document_title': f"Axoora FAQ — {faq.category}",
                'document_category': faq.category.lower(),
                'score': lexical,
            })

    scored_results.sort(key=lambda x: x['score'], reverse=True)
    return scored_results[:top_k]


def generate_rag_answer(query: str, retrieved_chunks: list[dict]) -> tuple[str, list[str], list[dict]]:
    """
    RAG Generation Phase:
    Synthesizes an answer using retrieved chunks as strict context.
    Uses Gemini/OpenAI if available, or deterministic grounded synthesis.
    Returns: (answer_text, source_titles, suggested_actions)
    """
    sources = list(dict.fromkeys(c['document_title'] for c in retrieved_chunks))

    # Base suggested actions
    suggested_actions = [
        {"label": "👤 Talk to Human Agent", "action": "escalate_human", "primary": True},
    ]

    # Context string preparation
    context_text = "\n\n".join(
        f"--- Source: {c['document_title']} ---\n{c['content']}"
        for c in retrieved_chunks
    )

    # 1. Try Google Gemini API if configured
    if GEMINI_API_KEY and retrieved_chunks:
        try:
            system_instruction = (
                "You are Axoora's AI Concierge, the official financial intelligence assistant for "
                "AXOORA Financial Technologies Limited (Licensed by the Central Bank of Nigeria, "
                "deposits insured by NDIC, located at Suite 08 Block C, Cappador Mall, 85 Aguiyi Ironsi Street Maitama, Abuja).\n"
                "Answer the user's question clearly, warmly, and concisely (2-4 sentences or bullet points) "
                "based ONLY on the provided context.\n"
                "Always mention key guarantees like CBN licensing, NDIC insurance, or ₦0 fees when relevant.\n"
                "If the context does not contain the answer, advise the customer that our human support officers "
                "are available and invite them to speak with a human agent."
            )

            prompt = (
                f"{system_instruction}\n\n"
                f"RELEVANT CONTEXT:\n{context_text}\n\n"
                f"CUSTOMER QUESTION: {query}\n\n"
                f"ANSWER:"
            )

            for model_name in ['gemini-flash-latest', 'gemini-2.5-flash-lite', 'gemini-3.8-flash']:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 400}
                    }
                    resp = requests.post(url, json=payload, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                        return text, sources, suggested_actions
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Gemini generation fallback triggered: {e}")

    # 2. Try OpenAI API if configured
    if OPENAI_API_KEY and retrieved_chunks:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are Axoora's AI Concierge. Answer questions using only the provided banking context. "
                        "Keep responses concise, polite, and accurate for Nigerian personal & business banking."
                    ),
                },
                {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"},
            ]
            payload = {"model": "gpt-4o-mini", "messages": messages, "temperature": 0.2, "max_tokens": 300}
            resp = requests.post(url, headers=headers, json=payload, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
                return text, sources, suggested_actions
        except Exception as e:
            logger.warning(f"OpenAI generation fallback triggered: {e}")

    # 3. Grounded Deterministic Synthesizer (Works 100% offline with zero dependencies)
    if retrieved_chunks:
        top_chunk = retrieved_chunks[0]
        summary_sentences = top_chunk['content'].split('. ')
        extracted = '. '.join(summary_sentences[:3])
        if not extracted.endswith('.'):
            extracted += '.'

        # Check for category-tailored recommendations
        category = top_chunk.get('document_category', '')
        if 'pos' in category:
            suggested_actions.insert(0, {"label": "Request Apex POS", "action": "open_apply", "interest": "pos-agent"})
        elif 'account' in category or 'fee' in category:
            suggested_actions.insert(0, {"label": "Open Account / Waitlist", "action": "open_waitlist"})
        elif 'islamic' in category:
            suggested_actions.insert(0, {"label": "Explore Save & Earn", "action": "quick_reply", "text": "How does Save and Earn work?"})

        answer = (
            f"{extracted}\n\n"
            f"Verified under Axoora's Central Bank of Nigeria (CBN) license. "
            f"If you need personalized account assistance, click 'Talk to Human Agent' to connect with our Maitama desk."
        )
        return answer, sources, suggested_actions

    # 4. Fallback when no knowledge chunks matched
    fallback_answer = (
        "Thank you for contacting Axoora Priority Support. "
        "I am Axoora's AI Concierge. I can answer questions about our ₦0 fee accounts, Apex 4G POS terminals, "
        "WhatsApp AI banking, non-interest Save & Earn, and security. "
        "If you would like to speak directly with an actual human support agent, click 'Talk to Human Agent' below!"
    )
    return fallback_answer, [], suggested_actions
