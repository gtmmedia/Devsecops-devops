"""Block until the database accepts connections (used before migrations)."""

import sys
import time

from sqlalchemy import text

from app.database import engine


def main(retries: int = 60, delay: float = 2.0) -> int:
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"database is ready (attempt {attempt})", flush=True)
            return 0
        except Exception as exc:
            print(
                f"waiting for database ({attempt}/{retries}): {exc.__class__.__name__}", flush=True
            )
            time.sleep(delay)
    print("database never became ready", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
