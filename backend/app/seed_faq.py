# backend/seed_faqs.py
from .faq import upsert_faqs


faqs = [
    {
        "question": "How do I reset my password?",
        "answer": "Go to Settings > Account > Reset Password. Enter your email; we will send a reset link.",
        "metadata": {"topic": "auth"},
    },
    {
        "question": "How do I update my billing card?",
        "answer": "Go to Billing > Payment Methods > Add Card or Edit existing card.",
        "metadata": {"topic": "billing"},
    },
]

upsert_faqs(faqs)
print("Inserted FAQs")
