import Initialize
import AutoComplete
import os


def main():
    # --- Setup for demonstration ---
    db_file = "autocomplete.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    if not os.path.exists("Archive/subdir"):
        os.makedirs("Archive/subdir")
    with open("Archive/file1.txt", "w") as f:
        f.write("This is a test sentence for the project.\n")
        f.write("Another test for auto-completion, what a fun project.\n")
        f.write("The quick brown fox jumps over the lazy dog.\n")
    with open("Archive/subdir/file2.txt", "w") as f:
        f.write("A sentence in a subdirectory for testing paths.\n")
        f.write("A different test of file paths in a sub dir.\n")
    # --- End of setup ---

    Initialize.initialize_database("Archive")

    current_input = ""
    print("Enter your text:")
    while True:
        try:
            user_input = input(current_input)
        except EOFError:
            break

        if user_input == '#':
            current_input = ""
            print("Enter your text:")
            continue

        current_input += user_input

        if current_input:
            suggestions = AutoComplete.get_best_k_completions(current_input)

            if suggestions:
                print("Here are 5 suggestions:")
                for i, suggestion in enumerate(suggestions):
                    file_name_with_ext = os.path.basename(suggestion.source_text)
                    file_name = os.path.splitext(file_name_with_ext)[0]
                    print(f"{i + 1}. {suggestion.completed_sentence} ({file_name} {suggestion.offset})")
            else:
                print("No suggestions found.")

        if current_input and user_input != '#':
            print(f"You can continue typing from '{current_input}'")


if __name__ == "__main__":
    main()