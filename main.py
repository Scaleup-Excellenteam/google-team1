from initialize import initialize_autocomplete_system
from autocomplete import AutoCompleteSystem

def main():
    """
    Main function for running the autocomplete CLI.
    Loads or builds the index cache, then interacts with the user to get prefixes and display suggestions.
    """
    acs = AutoCompleteSystem()

    # Initialize or load the cache
    initialize_autocomplete_system(acs)

    print("Enter your prefix, '#' to reset buffer.")
    buffer = ""

    # Interactive input loop
    while True:
        user_in = input(f"[{buffer}] > ")

        if user_in == "#":
            buffer = ""
            print("Buffer reset.")
            continue

        # Append user input to buffer with space if needed
        buffer += (" " if buffer and not user_in.startswith(" ") else "") + user_in

        completions = acs.get_best_k_completions(buffer)

        for i, c in enumerate(completions, 1):
            print(f"{i}. (score={c.score}) {c.completed_sentence} -- {c.source_text} (line {c.offset})")


if __name__ == "__main__":
    main()
