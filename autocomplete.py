import os
import string
import gzip
import pickle
from dataclasses import dataclass
from typing import List, Tuple, Dict

CACHE_FILE = "autocomplete_cache.pkl.gz"  # Compressed cache filename
_PUNCT_TABLE = str.maketrans('', '', string.punctuation)  # Translation table to remove punctuation

_SUB_PENALTIES = [5, 4, 3, 2, 1]  # Penalties for substitutions
_INSDEL_PENALTIES = [10, 8, 6, 4, 2]  # Penalties for insertions or deletions


@dataclass
class AutoCompleteData:
    """Data class for storing an autocomplete suggestion result."""
    completed_sentence: str  # The full sentence completion
    source_text: str  # Source file path from which the sentence was loaded
    offset: int  # Line number in the source file
    score: int  # Score representing the quality of the match


def normalize_text(s: str) -> str:
    """
    Normalize input text by removing punctuation, lowering case, and collapsing spaces.
    """
    return " ".join(s.translate(_PUNCT_TABLE).lower().split())


def penalty_for(kind: str, pos: int) -> int:
    """
    Return penalty score based on edit kind and position.
    """
    idx = pos - 1
    if kind == "substitution":
        return _SUB_PENALTIES[idx] if idx < len(_SUB_PENALTIES) else _SUB_PENALTIES[-1]
    if kind in ("insertion", "deletion"):
        return _INSDEL_PENALTIES[idx] if idx < len(_INSDEL_PENALTIES) else _INSDEL_PENALTIES[-1]
    return 0


def single_edit_match_info(prefix: str, candidate: str):
    """
    Check if prefix can be converted into candidate with a single edit.
    Returns ("exact", 0) if exact match,
    or (kind, position) if single edit match,
    or None if no match.
    """
    if prefix == candidate:
        return ("exact", 0)

    lp, lc = len(prefix), len(candidate)
    if abs(lp - lc) > 1:
        return None

    if lp == lc:
        diffs = [i for i in range(lp) if prefix[i] != candidate[i]]
        if len(diffs) == 1:
            return ("substitution", diffs[0] + 1)
        return None

    if lp + 1 == lc:
        i = 0
        while i < lp and prefix[i] == candidate[i]:
            i += 1
        if prefix[i:] == candidate[i + 1:]:
            return ("insertion", i + 1)
        return None

    if lp == lc + 1:
        i = 0
        while i < lc and prefix[i] == candidate[i]:
            i += 1
        if prefix[i + 1:] == candidate[i:]:
            return ("deletion", i + 1)
        return None

    return None


class AutoCompleteSystem:
    def __init__(self):
        """
        Initialize the autocomplete system.
        """
        self.sentences: List[Tuple[str, str, int]] = []
        self.word_index: Dict[str, List[int]] = {}


    def build_from_folder(self, root_folder: str):
        """
        Build index from all supported text files under root_folder.
        """
        print("Scanning files and loading sentences...")

        for dirpath, _, filenames in os.walk(root_folder):
            for fname in filenames:
                if not fname.lower().endswith('.txt'):
                    continue

                fullpath = os.path.join(dirpath, fname)
                try:
                    with open(fullpath, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f):
                            line_stripped = line.strip()
                            if not line_stripped:
                                continue

                            idx = len(self.sentences)
                            self.sentences.append((line_stripped, fullpath, i))

                            norm = normalize_text(line_stripped)
                            words = norm.split()

                            for w in words:
                                if len(w) == 2:
                                    # שמירה של מילה קצרה בשלמותה
                                    self.word_index.setdefault(w, []).append(idx)
                                else:
                                    # אינדוקס רגיל: קודם אורך 3
                                    for j in range(len(w) - 2):
                                        substring = w[j:j + 3]
                                        self.word_index.setdefault(substring, []).append(idx)
                                    # ואז 4–5
                                    for length in range(4, min(6, len(w) + 1)):
                                        for j in range(len(w) - length + 1):
                                            substring = w[j:j + length]
                                            self.word_index.setdefault(substring, []).append(idx)

                except Exception as e:
                    print(f"Warning: skipped {fullpath}: {e}")

        print(f"Loaded {len(self.sentences)} sentences, indexed {len(self.word_index)} prefixes.")

    def save_cache(self):
        """
        Save sentences and index to compressed cache file.
        """
        print(f"Saving cache to {CACHE_FILE}...")
        with gzip.open(CACHE_FILE, "wb") as f:
            pickle.dump((self.sentences, self.word_index), f)
        print("Cache saved.")

    def load_cache(self):
        """
        Load sentences and index from compressed cache file.
        """
        print(f"Loading cache from {CACHE_FILE}...")
        with gzip.open(CACHE_FILE, "rb") as f:
            self.sentences, self.word_index = pickle.load(f)
        print(f"Loaded {len(self.sentences)} sentences, indexed {len(self.word_index)} prefixes.")


    def get_best_k_completions(self, prefix: str) -> List[AutoCompleteData]:
        """
        Return top k best completions for the given prefix.
        """
        prefix_norm = normalize_text(prefix)
        if not prefix_norm:
            return []

        results = []
        lp = len(prefix_norm)

        first_word = prefix_norm.split()[0]
        candidate_idxs = set()

        # 🔹 טיפול במילים קצרות (אורך 2)
        if len(first_word) == 2:
            indices = self.word_index.get(first_word, [])
            candidate_idxs.update(indices)
        else:
            # אינדוקס רגיל 3–5 תווים
            for length in range(3, min(6, len(first_word) + 1)):
                if length <= len(first_word):
                    substring = first_word[:length]
                    indices = self.word_index.get(substring, [])
                    candidate_idxs.update(indices)

            # אם לא נמצאו — ניסיון נוסף עם 3 תווים ראשונים
            if not candidate_idxs and len(first_word) >= 3:
                substring = first_word[:3]
                candidate_idxs.update(self.word_index.get(substring, []))

        # אם אין התאמות ישירות — fallback לחיפוש בכל המשפטים
        if not candidate_idxs:
            print(f"No direct matches found for '{first_word}', checking all sentences for single edit matches...")
            candidate_idxs = set(range(len(self.sentences)))

        candidate_idxs = list(candidate_idxs)

        for idx in candidate_idxs:
            sentence, src, offset = self.sentences[idx]
            sentence_norm = normalize_text(sentence)

            if prefix_norm in sentence_norm:
                score = 2 * lp
                results.append(AutoCompleteData(sentence, src, offset, score))
                continue

            found = False
            for L in {lp, lp + 1, lp - 1}:
                if L <= 0 or L > len(sentence_norm):
                    continue

                for start in range(len(sentence_norm) - L + 1):
                    sub = sentence_norm[start:start + L]
                    info = single_edit_match_info(prefix_norm, sub)

                    if info and info[0] != "exact":
                        kind, pos = info
                        base_score = 2 * lp
                        score = base_score - penalty_for(kind, pos)
                        results.append(AutoCompleteData(sentence, src, offset, score))
                        found = True
                        break

                if found:
                    break

        results.sort(key=lambda x: (-x.score, x.completed_sentence.lower()))

        seen = set()
        final_results = []
        for r in results:
            key = r.completed_sentence
            if key not in seen:
                final_results.append(r)
                seen.add(key)
            if len(final_results) >= 5:
                break

        return final_results
