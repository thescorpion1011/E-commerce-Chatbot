from sentence_transformers import SentenceTransformer
import numpy as np

encoder = SentenceTransformer("BAAI/bge-small-en-v1.5")


faq_utterances = [
    "What is the return policy of the product?",
    "Do I get a discount with the HDFC Credit Card?",
    "How can I track my order?",
    "What payment methods are accepted?",
    "How long does it take to process a refund?",
    "What is your policy on defective products?"
]

sql_utterances = [
    "Find black Puma shoes priced between 5000 and 10000",
    "Show products under 5000 rupees",
    "What is the price of a product?",
    "Show products currently in stock",
    "Find the top selling products",
    "Show orders placed today"
]

routes = {
    "faq": faq_utterances,
    "sql": sql_utterances
}

route_embeddings = {
    name: encoder.encode(
        utterances,
        normalize_embeddings=True
    )
    for name, utterances in routes.items()
}


def router(query):
    query_embedding = encoder.encode(
        query,
        normalize_embeddings=True
    )

    scores = {}

    for name, embeddings in route_embeddings.items():
        similarity = embeddings @ query_embedding
        scores[name] = float(np.max(similarity))

    return max(scores, key=scores.get)


if __name__ == "__main__":
    print(router("What is your policy on defective products?"))
    print(router("Black Puma shoes in price range of 5000 to 10000"))
