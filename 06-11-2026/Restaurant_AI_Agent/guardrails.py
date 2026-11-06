import re

MAX_QUESTION_LENGTH = 500
MIN_GUESTS = 1
MAX_GUESTS = 20

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# 10-digit numbers, optionally with +country code and spaces/dashes, e.g. +91 98765 43210
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){9}\d(?!\w)")

RESTAURANT_KEYWORDS = {
    "restaurant", "restaurants", "food", "eat", "eating", "dine", "dining", "dinner",
    "lunch", "breakfast", "brunch", "meal", "cuisine", "menu", "table", "seat", "seats",
    "reserve", "reservation", "book", "booking", "cost", "price", "prices", "budget",
    "cheap", "expensive", "bill", "total", "guest", "guests", "people", "persons",
    "person", "party", "group", "veg", "vegetarian", "location", "hyderabad",
    "indian", "italian", "chinese", "japanese", "thai", "mexican", "mediterranean",
    "french", "korean", "continental", "kerala", "south", "north", "cafe", "bistro",
}

# Short follow-ups that only make sense with conversation context.
FOLLOW_UP_PATTERN = re.compile(
    r"^(yes|yeah|yep|yup|no|nope|ok|okay|sure|thanks|thank you|that one|the first one|"
    r"the second one|the last one|make (it|that).*|what if.*|how about.*|and .*|"
    r"\d+(\s*(people|persons|guests|pax))?)[.!?]*$",
    re.IGNORECASE,
)


def validate_input(question: str) -> str | None:
    """Return an error message if the question is empty or too long, else None."""
    if not question or not question.strip():
        return "Please enter a question."
    if len(question) > MAX_QUESTION_LENGTH:
        return f"Your question is too long. Please keep it under {MAX_QUESTION_LENGTH} characters."
    return None


def contains_pii(text: str) -> bool:
    """Detect email addresses and phone numbers."""
    return bool(EMAIL_PATTERN.search(text) or PHONE_PATTERN.search(text))


def redact_pii(text: str) -> str:
    """Replace email addresses and phone numbers with placeholders."""
    text = EMAIL_PATTERN.sub("[REDACTED EMAIL]", text)
    return PHONE_PATTERN.sub("[REDACTED PHONE]", text)


def is_follow_up(question: str) -> bool:
    """Allow short contextual replies such as 'yes', 'no' or '6 people'."""
    return bool(FOLLOW_UP_PATTERN.match(question.strip()))


def is_restaurant_related(question: str, restaurant_names: list[str]) -> bool:
    """Allow only restaurant-related questions (or follow-ups to them)."""
    text = question.lower()
    words = set(re.findall(r"[a-z]+", text))
    if words & RESTAURANT_KEYWORDS:
        return True
    if any(name.lower() in text for name in restaurant_names):
        return True
    return is_follow_up(question)


def validate_guests(guests: int) -> str | None:
    """Return an error message if the guest count is out of range, else None."""
    if guests < MIN_GUESTS or guests > MAX_GUESTS:
        return f"Guest count must be between {MIN_GUESTS} and {MAX_GUESTS}. You asked for {guests}."
    return None


def check_question(question: str, restaurant_names: list[str]) -> str | None:
    """Run all input guardrails. Return a rejection message, or None if allowed."""
    error = validate_input(question)
    if error:
        return error
    if contains_pii(question):
        return ("PII detected: please don't share email addresses or phone numbers. "
                "Your message was not processed.")
    if not is_restaurant_related(question, restaurant_names):
        return "Sorry, I can only help with restaurant searches and dining-cost estimates."
    return None
