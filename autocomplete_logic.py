import os
from typing import List, Tuple, Optional
from initialize import Trie, AutoCompleteData, normalize_text


def calculate_score(matched_length: int, correction_type: int, correction_position: int) -> int:
    """
    Calculates the score for a given match based on the project's scoring rules.
    matched_length: The number of characters that match the prefix before corrections.
    """
    base_score = matched_length * 2
    score = base_score

    if correction_type == 1:  # Character replacement
        if correction_position == 1:
            score -= 5
        elif correction_position == 2:
            score -= 4
        elif correction_position == 3:
            score -= 3
        elif correction_position == 4:
            score -= 2
        else:
            score -= 1
    elif correction_type in (2, 3):  # Character addition or deletion
        if correction_position == 1:
            score -= 10
        elif correction_position == 2:
            score -= 8
        elif correction_position == 3:
            score -= 6
        elif correction_position == 4:
            score -= 4
        else:
            score -= 2

    return score


def find_best_match(normalized_sentence: str, normalized_prefix: str) -> Optional[Tuple[int, int]]:
    """
    Finds the best match (direct or with one correction) for the normalized prefix within the normalized sentence.
    Returns a tuple of (correction_type, correction_position) or None if no match.
    """
    prefix_len = len(normalized_prefix)
    sentence_len = len(normalized_sentence)

    # Direct substring match
    if normalized_prefix in normalized_sentence:
        return 0, 0

    # One correction match
    for i in range(sentence_len):
        # Replacement or no correction
        if i + prefix_len <= sentence_len:
            window = normalized_sentence[i: i + prefix_len]
            diff_count = 0
            diff_pos = -1
            for j in range(prefix_len):
                if normalized_prefix[j] != window[j]:
                    diff_count += 1
                    diff_pos = j + 1
            if diff_count == 1:
                return 1, diff_pos

        # Deletion
        if i + prefix_len - 1 <= sentence_len and prefix_len > 0:
            window = normalized_sentence[i: i + prefix_len - 1]
            for j in range(prefix_len):
                temp_prefix = normalized_prefix[:j] + normalized_prefix[j + 1:]
                if window == temp_prefix:
                    return 3, j + 1

        # Addition
        if i + prefix_len + 1 <= sentence_len:
            window = normalized_sentence[i: i + prefix_len + 1]
            for j in range(len(window)):
                temp_window = window[:j] + window[j + 1:]
                if temp_window == normalized_prefix:
                    return 2, j + 1

    return None


def get_best_k_completions(trie: Trie, prefix: str) -> List[AutoCompleteData]:
    """
    Retrieves the top 5 sentence completions based on the given prefix, using the Trie.
    """
    completions: List[AutoCompleteData] = []
    normalized_prefix = normalize_text(prefix)

    # In this approach, we scan all sentences (retrieved from the Trie) to find matches, including those with a correction.
    all_sentences = trie.search_for_completions("")

    for completion_data in all_sentences:
        match_info = find_best_match(normalize_text(completion_data.completed_sentence), normalized_prefix)
        if match_info:
            correction_type, correction_position = match_info

            matched_length = len(normalized_prefix)
            if correction_type == 3:
                matched_length -= 1

            score = calculate_score(matched_length, correction_type, correction_position)

            completions.append(AutoCompleteData(
                completion_data.completed_sentence,
                completion_data.source_text,
                completion_data.offset,
                score
            ))

    completions.sort(key=lambda x: (-x.score, x.completed_sentence))

    return completions[:5]