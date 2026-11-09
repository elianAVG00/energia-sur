"""Start the local backend with a process-local CU06 confirmation key."""

import os
import secrets


def main() -> None:
    # Compose runs one backend instance; externally configured keys override this.
    if not os.environ.get("CU06_CONFIRMATION_SECRET"):
        os.environ["CU06_CONFIRMATION_SECRET"] = secrets.token_hex(32)
    os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])


if __name__ == "__main__":
    main()
