"""Load demo tickets so the UI isn't empty:  python -m app.seed"""

from app.database import SessionLocal
from app.models import Comment, Ticket

SAMPLES = [
    (
        "Invoice #4821 shows the wrong amount",
        "We were charged twice for the March plan.",
        "high",
        "open",
        "Asha Rao",
        "asha@example.com",
        None,
    ),
    (
        "Can't reset my password",
        "The reset email never arrives, I checked spam.",
        "high",
        "in_progress",
        "Marcus Lee",
        "marcus@example.com",
        "Priya",
    ),
    (
        "Export to CSV is missing a column",
        "The 'created by' column is gone since last week.",
        "medium",
        "open",
        "Dana Whitfield",
        "dana@example.com",
        None,
    ),
    (
        "Dark mode request",
        "Would love a dark theme for night shifts.",
        "low",
        "open",
        "Tomás Ortega",
        "tomas@example.com",
        None,
    ),
    (
        "Login page loads slowly",
        "Takes about 8 seconds on mobile data.",
        "medium",
        "in_progress",
        "Mei Tanaka",
        "mei@example.com",
        "Rahul",
    ),
    (
        "Update billing address",
        "We moved offices, need the invoice address changed.",
        "low",
        "resolved",
        "Lucas Meyer",
        "lucas@example.com",
        "Priya",
    ),
    (
        "API returns 500 on bulk import",
        "POST /import fails with 500 for files above 5 MB.",
        "high",
        "in_progress",
        "Sofia Rossi",
        "sofia@example.com",
        "Rahul",
    ),
    (
        "Add a teammate to our account",
        "Please add jo@example.com as an admin.",
        "low",
        "closed",
        "Ivan Petrov",
        "ivan@example.com",
        "Priya",
    ),
    (
        "Notification emails arrive twice",
        "Every assignment email is duplicated.",
        "medium",
        "open",
        "Grace Okafor",
        "grace@example.com",
        None,
    ),
    (
        "Mobile app crashes on startup",
        "Android 14, crashes right after the splash screen.",
        "high",
        "open",
        "Noah Kim",
        "noah@example.com",
        None,
    ),
]


def main() -> None:
    with SessionLocal() as db:
        if db.query(Ticket).count():
            print("tickets already present, skipping seed")
            return
        for title, desc, prio, status, name, email, assignee in SAMPLES:
            ticket = Ticket(
                title=title,
                description=desc,
                priority=prio,
                status=status,
                requester_name=name,
                requester_email=email,
                assignee=assignee,
            )
            if assignee:
                ticket.comments.append(
                    Comment(author=assignee, body="Thanks for reporting this, I'm looking into it.")
                )
            db.add(ticket)
        db.commit()
        print(f"seeded {len(SAMPLES)} tickets")


if __name__ == "__main__":
    main()
