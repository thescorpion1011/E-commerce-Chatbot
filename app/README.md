# E-commerce Chatbot

An AI-powered e-commerce chatbot built with **Streamlit, Groq, ChromaDB, Sentence Transformers, and SQLite**. It answers frequently asked questions and retrieves product information from a SQLite database using natural-language queries.

## Features

- **FAQ Assistant:** Answers common questions about returns, refunds, payments, order tracking, and exchanges.
- **Semantic Routing:** Uses Sentence Transformers to classify user queries and route them to the appropriate handler.
- **Product Search:** Converts natural-language questions into SQL queries to retrieve product information.
- **AI-Generated Responses:** Uses the Groq API to generate conversational answers and format product results.
- **Vector Search:** Uses ChromaDB to retrieve relevant FAQ information.
- **Interactive Interface:** Provides a chat-based interface built with Streamlit.

## Tech Stack

- Python
- Streamlit
- Groq API
- Sentence Transformers
- ChromaDB
- SQLite
- Pandas
- NumPy
- python-dotenv

## Project Structure

```text
project-ecommerce-tool/
├── app/
│   ├── main.py
│   ├── router.py
│   ├── faq.py
│   ├── sql.py
│   ├── db.sqlite
│   └── resources/
│       └── faq_data.csv
├── .env
├── .gitignore
└── requirements.txt
```

## How It Works

1. The user enters a question in the Streamlit chat interface.
2. The semantic router uses Sentence Transformers to classify the question as an FAQ or product/database query.
3. For FAQ queries, ChromaDB retrieves relevant FAQ information, and Groq generates a natural-language answer.
4. For product queries, Groq generates an SQL query that retrieves information from the SQLite database.
5. The chatbot presents the result to the user.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/thescorpion1011/E-commerce-Chatbot
cd YOUR_REPOSITORY
```

Replace the repository URL with your actual GitHub repository URL.

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the location expected by your Python modules. For the configuration described in this project, use `app/.env` if your modules load it from the `app` directory.

Add:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_supported_groq_model
```

Replace the placeholder values with your actual Groq API key and a model available to your account.

**Security:** Never upload your `.env` file or API key to GitHub. Keep `.env` listed in `.gitignore`.

### 5. Prepare the Database and FAQ Data

- Ensure `app/db.sqlite` contains the required `product` table and product data.
- Ensure `app/resources/faq_data.csv` exists and contains the FAQ data in the format expected by `faq.py`.

The product table is expected to contain these columns:

- `product_link`
- `title`
- `brand`
- `price`
- `discount`
- `avg_rating`
- `total_ratings`

## Run the Application

From the project root, run:

```bash
streamlit run app/main.py
```

Streamlit will display a local URL in the terminal. Open that URL in your browser to use the chatbot.

## Example Queries

### FAQ Queries

- What is the return policy?
- How can I track my order?
- How long does a refund take?
- Can I exchange a damaged product?

### Product Queries

- Show me products under ₹5,000.
- Find Nike products.
- Show products with ratings above 4.5.
- Find Puma shoes priced between ₹5,000 and ₹10,000.

The available answers depend on the FAQ CSV, product database, and Groq model configuration.

## Security and Limitations

- Keep API keys and other secrets out of source control.
- Use a read-only SQLite connection for product searches wherever possible.
- Validate generated SQL before executing it.
- LLM-generated SQL can be incorrect; validate query behavior before relying on the results.
- The default Sentence Transformer model may need to download from Hugging Face on first use.
- This project is intended as a learning project. Production deployment would require additional security, testing, error handling, and database access controls.

## Future Improvements

- Add order-status lookup with secure customer authentication.
- Improve semantic routing and confidence thresholds.
- Add product filters and pagination.
- Add automated tests and structured logging.
- Deploy the application to a cloud platform.

## Author

Ashish Yadav

GitHub:https://github.com/thescorpion1011

---

*Built as a learning project to explore LLM applications, semantic search, natural-language-to-SQL workflows, and conversational AI.*