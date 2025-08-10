import os
import re
from typing import List
from dataclasses import dataclass
import string
import pickle
import sys

sys.setrecursionlimit(3000)

# The name of the file where we will store the Trie structure
TRIE_DATA_FILE = "trie_data.pkl"


@dataclass
class AutoCompleteData:
    completed_sentence: str
    source_text: str
    offset: int
    score: int


class TrieNode:
    """A node in the Trie data structure."""

    def __init__(self):
        self.children = {}
        # Stores a list of AutoCompleteData objects for sentences ending at this node.
        self.completions: List[AutoCompleteData] = []


class Trie:
    """The Trie data structure for efficient prefix searching."""

    def __init__(self):
        self.root = TrieNode()

    def insert(self, sentence: str, source_file: str, offset: int):
        """
        Inserts a sentence and its metadata into the Trie.
        """
        normalized_sentence = normalize_text(sentence)
        node = self.root

        for char in normalized_sentence:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]

        # Store the completion data at the end of the sentence's path.
        node.completions.append(AutoCompleteData(sentence, source_file, offset, 0))

    def search_for_completions(self, normalized_prefix: str) -> List[AutoCompleteData]:
        """
        Finds all possible completions for a given normalized prefix.
        Returns a list of all AutoCompleteData objects from the relevant sub-tree.
        """
        node = self.root
        for char in normalized_prefix:
            if char in node.children:
                node = node.children[char]
            else:
                return []

        # Collect all completions from this node and its children.
        completions = []
        self._collect_all_completions(node, completions)
        return completions

    def _collect_all_completions(self, node: TrieNode, completions: List[AutoCompleteData]):
        """
        Recursively collects all completions from a node and its descendants.
        """
        completions.extend(node.completions)
        for child in node.children.values():
            self._collect_all_completions(child, completions)


def normalize_text(text: str) -> str:
    """
    Normalizes a string by converting it to lowercase, removing all punctuation, and handling multiple spaces.
    """
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def initialize_trie(root_folder: str) -> Trie:
    """
    Initializes and builds the Trie from files, or loads it from a saved file.
    """
    if os.path.exists(TRIE_DATA_FILE):
        print("Loading the Trie from a saved file...")
        try:
            with open(TRIE_DATA_FILE, 'rb') as f:
                trie = pickle.load(f)
            print("The system is ready.")
            return trie
        except Exception as e:
            print(f"Could not load Trie from file: {e}. Rebuilding from scratch.")
            os.remove(TRIE_DATA_FILE)  # Deleting a corrupted file

    print("Loading the files and preparing the system...")
    trie = Trie()
    total_sentences = 0
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        sentence = line.strip()
                        if sentence:
                            trie.insert(sentence, file_path, i + 1)
                            total_sentences += 1
                print(filename)
            except Exception as e:
                print(f"Could not read file {file_path}: {e}")

    print(f"The system is ready. Loaded {total_sentences} sentences.")

    # Saving the Trie to a file
    try:
        with open(TRIE_DATA_FILE, 'wb') as f:
            pickle.dump(trie, f)
        print(f"Trie saved to {TRIE_DATA_FILE}.")
    except Exception as e:
        print(f"Could not save Trie to file: {e}")

    return trie