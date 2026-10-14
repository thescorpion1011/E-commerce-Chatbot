
import os
import re
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from groq import Groq


# ==================================================
# 1. CONFIGURATION
# ==================================================

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "db.sqlite"
ENV_PATH = APP_DIR / ".env"

load_dotenv(ENV_PATH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from app/.env")

if not GROQ_MODEL:
    raise ValueError("GROQ_MODEL is missing from app/.env")

client_sql = Groq(api_key=GROQ_API_KEY)


# ==================================================
# 2. DATABASE SCHEMA AND PROMPTS
# ==================================================

SQL_PROMPT = """
You generate SQLite SELECT queries for an e-commerce product database.

Table: product

Columns:
- product_link: product URL
- title: product name
- brand: brand name
- price: price in Indian Rupees
- discount: decimal discount (0.1 = 10%)
- avg_rating: average rating from 0 to 5
- total_ratings: number of ratings

Rules:
1. Generate exactly one SQLite SELECT query.
2. Always use SELECT *.
3. Query only the product table.
4. For brand matching, use
   LOWER(brand) LIKE LOWER('%brand_name%').
5. Never use ILIKE.
6. Use LIMIT when the user specifies a number of products.
7. For highest-rated products, use ORDER BY avg_rating DESC.
8. Use only the columns listed in the schema.
9. Generate read-only queries only.
10. Return exactly this format:

<SQL>SELECT * FROM product LIMIT 3</SQL>

Return no explanation or Markdown code fences.
"""

ANSWER_PROMPT = """
You are a helpful e-commerce shopping assistant.

Answer the user's question using only the supplied database records.
Never invent product details, prices, ratings, discounts, or links.

For product searches, list each product separately:

1. Product title
   Brand: brand name
   Price: Rs. price
   Discount: percentage
   Rating: average rating
   Total ratings: number
   Product link: clickable Markdown link

Convert a decimal discount to a percentage.
If the discount is missing, say it is unavailable.
If no records are provided, explain that no matching products were found.
Use natural, concise language.
"""


# ==================================================
# 3. GENERATE SQL QUERY
# ==================================================

def generate_sql_query(question):
    completion = client_sql.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SQL_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0,
        max_tokens=512,
    )

    return completion.choices[0].message.content or ""


# ==================================================
# 4. VALIDATE AND EXECUTE SQL
# ==================================================

def extract_sql(generated_text):
    """Extract one SQL query from the model response."""

    match = re.fullmatch(
        r"\s*<SQL>\s*(.*?)\s*</SQL>\s*",
        generated_text,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        raise ValueError("The generated SQL is missing SQL tags.")

    query = match.group(1).strip()

    # Allow one optional trailing semicolon only.
    query = query.rstrip().removesuffix(";").strip()

    if not query:
        raise ValueError("The generated SQL query is empty.")

    # Basic read-only validation.
    if not re.match(r"^SELECT\b", query, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")

    # Reject multiple statements and SQL comments.
    if ";" in query or "--" in query or "/*" in query:
        raise ValueError("Multiple statements or comments are not allowed.")

    if re.search(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|"
        r"PRAGMA|REPLACE|VACUUM|REINDEX)\b",
        query,
        re.IGNORECASE,
    ):
        raise ValueError("A prohibited SQL operation was detected.")

    # Restrict table references to product.
    tables = re.findall(
        r"\b(?:FROM|JOIN)\s+([a-zA-Z_]\w*)",
        query,
        re.IGNORECASE,
    )

    if not tables or any(
        table.lower() != "product" for table in tables
    ):
        raise ValueError("Only the product table may be queried.")

    # Require the expected output columns.
    if not re.match(r"^SELECT\s+\*", query, re.IGNORECASE):
        raise ValueError("The query must use SELECT *.")

    return query


def run_query(generated_text):
    """Execute a validated query against the database read-only."""

    if not DB_PATH.is_file():
        raise FileNotFoundError(
            f"Database file not found: {DB_PATH}"
        )

    query = extract_sql(generated_text)

    # Open the database in read-only mode.
    db_uri = DB_PATH.resolve().as_uri() + "?mode=ro"

    with sqlite3.connect(db_uri, uri=True) as connection:
        connection.execute("PRAGMA query_only = ON")

        # Verify the product table exists.
        table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'product'
            """
        ).fetchone()

        if table is None:
            raise ValueError(
                "The product table does not exist in this database."
            )

        # Validate columns against the real database schema.
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(product)"
            ).fetchall()
        }

        required_columns = {
            "product_link",
            "title",
            "brand",
            "price",
            "discount",
            "avg_rating",
            "total_ratings",
        }

        if not required_columns.issubset(columns):
            raise ValueError(
                "The product table columns do not match the expected schema."
            )

        return pd.read_sql_query(query, connection)


# ==================================================
# 5. GENERATE NATURAL-LANGUAGE ANSWER
# ==================================================

def data_comprehension(question, context):
    completion = client_sql.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": ANSWER_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Question:\n{question}\n\n"
                    f"Database records:\n{context}"
                ),
            },
        ],
        temperature=0,
        max_tokens=1200,
    )

    return (
        completion.choices[0].message.content or ""
    ).strip()


# ==================================================
# 6. COMPLETE SQL CHAIN
# ==================================================

def sql_chain(question):
    try:
        # Step 1: Generate SQL.
        generated_sql = generate_sql_query(question)

        # Step 2: Execute the validated query.
        df = run_query(generated_sql)

        # Step 3: Handle empty results.
        if df.empty:
            return "Sorry, no products matched your search."

        # Step 4: Convert records to JSON-friendly values.
        records = df.astype(object).where(
            pd.notna(df), None
        ).to_dict(orient="records")

        # Step 5: Generate a customer-friendly answer.
        return data_comprehension(question, records)

    except (ValueError, FileNotFoundError, sqlite3.Error) as error:
        print(f"SQL processing error: {error}")
        return (
            "Sorry, I couldn't complete that product search. "
            "Please try rephrasing your question."
        )

    except Exception as error:
        print(f"Unexpected chatbot error: {error}")
        return (
            "Sorry, something went wrong while searching for products."
        )


# ==================================================
# 7. TEST SQL.PY INDEPENDENTLY
# ==================================================

if __name__ == "__main__":
    question = "Show me 3 Nike shoes with ratings higher than 4.7"

    print("Question:", question)
    print("Answer:")
    print(sql_chain(question))
