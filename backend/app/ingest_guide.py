"""One-off guide ingestion command (no secrets are printed)."""

import argparse
from pathlib import Path

from app.guide_store import ingest_guide


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest the approved Edesur guide.")
    parser.add_argument("path", nargs="?", type=Path, default=None)
    parser.add_argument("--force", action="store_true",
                        help="Allow re-ingesting an older version or changed content.")
    args = parser.parse_args()
    result = ingest_guide(args.path, force=args.force)
    print(
        f"{result.outcome}: {result.document_id} {result.version} "
        f"({result.article_count} articles)",
    )


if __name__ == "__main__":
    main()
