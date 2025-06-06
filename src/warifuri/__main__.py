"""Entry point for python -m warifuri."""

from .cli.main import cli


def main() -> None:
    """Main entry point for console scripts."""
    cli()


if __name__ == "__main__":
    main()
