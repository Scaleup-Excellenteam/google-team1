import os
from initialize import initialize_trie
from autocomplete_logic import get_best_k_completions

if __name__ == "__main__":
    # --- Setup for demonstration ---
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

    trie = initialize_trie("Archive")

    current_input = ""
    print("Enter your text:")
    while True:
        try:
            user_input = input(f"{current_input}> ")
        except EOFError:
            break

        if user_input == '#':
            current_input = ""
            print("Enter your text:")
            continue

        current_input += user_input

        if current_input:
            suggestions = get_best_k_completions(trie, current_input)

            if suggestions:
                print("Here are 5 suggestions:")
                for i, suggestion in enumerate(suggestions):
                    file_name_with_ext = os.path.basename(suggestion.source_text)
                    file_name = os.path.splitext(file_name_with_ext)[0]
                    print(f"{i + 1}. {suggestion.completed_sentence} ({file_name} {suggestion.offset})")
            else:
                print("No suggestions found.")