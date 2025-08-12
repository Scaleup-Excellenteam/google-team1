import unittest
import tempfile
import os
import shutil
import time
from autocomplete import AutoCompleteSystem, normalize_text, single_edit_match_info


class TestCriticalLogic(unittest.TestCase):
    """Test core functions that could break easily"""

    def test_normalize_edge_cases(self):
        """Test text normalization with problematic inputs"""
        self.assertEqual(normalize_text(""), "")
        self.assertEqual(normalize_text("!@#$%"), "")
        self.assertEqual(normalize_text("   \t\n  "), "")
        self.assertEqual(normalize_text("Hello,  World!"), "hello world")

    def test_single_edit_boundaries(self):
        """Test single edit matching at edge cases"""
        # Exact match
        self.assertEqual(single_edit_match_info("abc", "abc"), ("exact", 0))

        # Substitutions at different positions
        self.assertEqual(single_edit_match_info("abc", "xbc"), ("substitution", 1))
        self.assertEqual(single_edit_match_info("abc", "abx"), ("substitution", 3))

        # Should fail - too many changes
        self.assertIsNone(single_edit_match_info("abc", "xyz"))
        self.assertIsNone(single_edit_match_info("a", "abcde"))


class TestScoringAccuracy(unittest.TestCase):
    """Test scoring matches project spec exactly"""

    def setUp(self):
        self.acs = AutoCompleteSystem()
        self.test_dir = tempfile.mkdtemp()

        with open(os.path.join(self.test_dir, "test.txt"), 'w') as f:
            f.write("To be or not to be, that is the question\n")

        self.acs.build_from_folder(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_spec_examples(self):
        """Test exact examples from specification"""
        test_cases = [
            ("to be", 10),  # 2*5 = 10
            ("to pe", 8),  # 2*5 - 2 = 8 (fourth char sub)
        ]

        for query, expected_score in test_cases:
            results = self.acs.get_best_k_completions(query)
            found = any(r.score == expected_score and "To be" in r.completed_sentence
                        for r in results)
            self.assertTrue(found, f"Query '{query}' should score {expected_score}")


class TestIndexingSystem(unittest.TestCase):
    """Test complex indexing logic"""

    def setUp(self):
        self.acs = AutoCompleteSystem()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_short_word_handling(self):
        """Test special 2-character word indexing"""
        with open(os.path.join(self.test_dir, "test.txt"), 'w') as f:
            f.write("to be or not\n")

        self.acs.build_from_folder(self.test_dir)

        # 2-char words should be indexed completely
        self.assertIn("to", self.acs.word_index)
        self.assertIn("be", self.acs.word_index)
        self.assertIn("or", self.acs.word_index)

    def test_fallback_mechanism(self):
        """Test fallback when no direct matches"""
        with open(os.path.join(self.test_dir, "test.txt"), 'w') as f:
            f.write("unique sentence here\n")

        self.acs.build_from_folder(self.test_dir)

        # Should find via fallback even without direct index match
        results = self.acs.get_best_k_completions("znique")  # "unique" with typo
        found = any("unique" in r.completed_sentence for r in results)
        self.assertTrue(found, "Fallback should find single-edit matches")


class TestComplexQueries(unittest.TestCase):
    """Test scenarios that could break the system"""

    def setUp(self):
        self.acs = AutoCompleteSystem()
        self.test_dir = tempfile.mkdtemp()

        with open(os.path.join(self.test_dir, "test.txt"), 'w') as f:
            f.write("Hello world programming\n")
            f.write("Python is awesome\n")
            f.write("Machine learning algorithms\n")

        self.acs.build_from_folder(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_empty_query(self):
        """Test empty/whitespace queries"""
        self.assertEqual(len(self.acs.get_best_k_completions("")), 0)
        self.assertEqual(len(self.acs.get_best_k_completions("   ")), 0)

    def test_no_matches(self):
        """Test queries with no possible matches"""
        results = self.acs.get_best_k_completions("zxqwerty")
        self.assertLessEqual(len(results), 5)

    def test_results_limit(self):
        """Test max 5 results and proper sorting"""
        results = self.acs.get_best_k_completions("a")

        # Should not exceed 5 results
        self.assertLessEqual(len(results), 5)

        # Should be sorted by score descending
        for i in range(len(results) - 1):
            self.assertGreaterEqual(results[i].score, results[i + 1].score)

class TestSearchTimeLimit(unittest.TestCase):
    """
    Unit test class to verify that search queries in the autocomplete system
    complete within a specified time limit.

    This ensures the system remains responsive and avoids excessively long
    searches that degrade user experience.
    """
    def setUp(self):
        self.acs = AutoCompleteSystem()
        self.test_dir = tempfile.mkdtemp()

        text_content = "\n".join([
            "Hello world programming",
            "Python is awesome",
            "Machine learning algorithms",
            "To be or not to be, that is the question",
            "Testing autocomplete system with various words",
            "Performance measurement and benchmarking",
            "Short words go here",
            "Extraordinary extraordinary examples"
        ])
        with open(os.path.join(self.test_dir, "test.txt"), 'w') as f:
            f.write(text_content)

        self.acs.build_from_folder(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_search_time_limit(self):
        queries = [
            "to",
            "python",
            "extra",
            "notto",
            "zxqwerty",
            "a"
        ]

        for q in queries:
            start = time.perf_counter()
            results = self.acs.get_best_k_completions(q)
            duration = time.perf_counter() - start
            self.assertLessEqual(duration, 5, f"Search for '{q}' took too long: {duration:.2f}s")


if __name__ == '__main__':
    unittest.main(verbosity=2)