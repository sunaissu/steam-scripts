import sys
from dotenv import load_dotenv

load_dotenv()

from scripts import check_full_discount_games


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "check_full_discount_games"

    if command == "check_full_discount_games":
        check_full_discount_games.run()
    else:
        print(f"Unknown command: '{command}'")
        print("Available commands: check_full_discount_games")
        sys.exit(1)


if __name__ == "__main__":
    main()
