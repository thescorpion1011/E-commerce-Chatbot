
import os
import pandas as pd
import chromadb

from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

# Load .env from the app directory
load_dotenv(Path(__file__).parent / ".env")

# Initialize Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = os.getenv("GROQ_MODEL")

if not GROQ_MODEL:
    raise ValueError("GROQ_MODEL is missing from your .env file")

# Paths and database
faqs_path = Path(__file__).parent / "resources" / "faq_data.csv"

chroma_client = chromadb.Client()
collection_name_faq = "faqs"


def ingest_faq_data(path):
    existing = [
        c.name for c in chroma_client.list_collections()
    ]

    if collection_name_faq not in existing:
        df = pd.read_csv(path)

        docs = df["question"].fillna("").astype(str).tolist()
        answers = df["answer"].fillna("").astype(str).tolist()

        metadata = [
            {"answer": answer}
            for answer in answers
        ]

        ids = [f"id_{i}" for i in range(len(docs))]

        collection = chroma_client.create_collection(
            name=collection_name_faq
        )

        collection.add(
            documents=docs,
            metadatas=metadata,
            ids=ids
        )

        print("FAQ data successfully ingested.")
    else:
        print("FAQ collection already exists.")


def get_relevant_qa(query):
    collection = chroma_client.get_collection(
        name=collection_name_faq
    )

    return collection.query(
        query_texts=[query],
        n_results=2
    )


def generate_answer(query, context):
    prompt = f"""
You are an e-commerce customer support assistant.

Answer the customer's question using only the FAQ context.
Be polite, clear, and concise.
Do not invent policies or information.
If the answer is not available in the context, say:
"Sorry, I couldn't find that information in our FAQs."

CUSTOMER QUESTION:
{query}

FAQ CONTEXT:
{context}

Provide a natural-language answer:
"""

    completion = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful e-commerce support assistant. "
                    "Use only the provided FAQ context."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return completion.choices[0].message.content.strip()


def faq_chain(query):
    result = get_relevant_qa(query)

    metadata = result.get("metadatas", [[]])[0]

    answers = [
        item["answer"]
        for item in metadata
        if item and item.get("answer")
    ]

    if not answers:
        return "Sorry, I couldn't find that information in our FAQs."

    context = "\n".join(answers)

    # Generate a natural-language answer instead of returning
    # the raw ChromaDB dictionary.
    return generate_answer(query, context)


if __name__ == "__main__":
    ingest_faq_data(faqs_path)

    query = "What's your policy on defective products?"

    answer = faq_chain(query)

    print("Answer:", answer)
