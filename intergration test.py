import unittest
import tempfile
import os
import shutil
from unittest.mock import patch
from autocomplete import AutoCompleteSystem
from initialize import initialize_autocomplete_system


class TestCacheIntegrity(unittest.TestCase):
    """Test cache save/load operations"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.test_dir, "test_cache.pkl.gz")

        # Patch cache location
        import autocomplete
        self.original_cache = autocomplete.CACHE_FILE
        autocomplete.CACHE_FILE = self.cache_file

        self.acs = AutoCompleteSystem()

    def tearDown(self):
        import autocomplete
        autocomplete.CACHE_FILE = self.original_cache
        shutil.rmtree(self.test_dir)

    def test_save_load_cycle(self):
        """Test complete cache cycle preserves data"""
        # Create test data
        with open(os.path.join(self.test_dir, "test.txt"), 'w') as f:
            f.write("Test sentence here\n")
            f.write("Another test line\n")

        self.acs.build_from_folder(self.test_dir)
        original_count = len(self.acs.sentences)

        # Save and reload
        self.acs.save_cache()
        new_acs = AutoCompleteSystem()
        new_acs.load_cache()

        # Verify data integrity
        self.assertEqual(len(new_acs.sentences), original_count)
        self.assertEqual(len(new_acs.word_index), len(self.acs.word_index))

        # Verify functionality works the same
        original_results = self.acs.get_best_k_completions("test")
        new_results = new_acs.get_best_k_completions("test")
        self.assertEqual(len(original_results), len(new_results))


class TestInitializationFlow(unittest.TestCase):
    """Test initialization logic"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.test_dir, "test_cache.pkl.gz")

        # Patch both autocomplete and initialize modules
        import autocomplete
        import initialize
        self.original_cache = autocomplete.CACHE_FILE
        autocomplete.CACHE_FILE = self.cache_file
        initialize.CACHE_FILE = self.cache_file

    def tearDown(self):
        import autocomplete
        import initialize
        autocomplete.CACHE_FILE = self.original_cache
        initialize.CACHE_FILE = self.original_cache
        shutil.rmtree(self.test_dir)

    def test_init_without_cache(self):
        """Test initialization builds from folder when no cache"""
        with open(os.path.join(self.test_dir, "test.txt"), 'w') as f:
            f.write("Test content here\n")

        acs = AutoCompleteSystem()

        with patch('sys.argv', ['main.py', self.test_dir]):
            initialize_autocomplete_system(acs)

        # Should build system and create cache
        self.assertGreater(len(acs.sentences), 0)
        self.assertTrue(os.path.exists(self.cache_file))

    def test_init_with_existing_cache(self):
        """Test initialization uses existing cache"""
        # Create cache first
        acs1 = AutoCompleteSystem()
        acs1.sentences = [("Test", "file.txt", 0)]
        acs1.word_index = {"test": [0]}
        acs1.save_cache()

        # Initialize new system
        acs2 = AutoCompleteSystem()
        initialize_autocomplete_system(acs2)

        # Should load from cache
        self.assertEqual(len(acs2.sentences), 1)
        self.assertEqual(acs2.sentences[0][0], "Test")


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete system workflow"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.test_dir, "test_cache.pkl.gz")

        # Patch both modules
        import autocomplete
        import initialize
        self.original_cache = autocomplete.CACHE_FILE
        autocomplete.CACHE_FILE = self.cache_file
        initialize.CACHE_FILE = self.cache_file

        # Create test files with spec examples
        with open(os.path.join(self.test_dir, "shakespeare.txt"), 'w') as f:
            f.write("To be or not to be, that is the question\n")

        with open(os.path.join(self.test_dir, "programming.txt"), 'w') as f:
            f.write("Hello world example\n")
            f.write("Python programming language\n")

    def tearDown(self):
        import autocomplete
        import initialize
        autocomplete.CACHE_FILE = self.original_cache
        initialize.CACHE_FILE = self.original_cache
        shutil.rmtree(self.test_dir)

    def test_complete_workflow(self):
        """Test full initialization and query workflow"""
        acs = AutoCompleteSystem()

        with patch('sys.argv', ['main.py', self.test_dir]):
            initialize_autocomplete_system(acs)

        # Test key scenarios from spec
        results = acs.get_best_k_completions("to be")
        shakespeare_found = any("To be or not" in r.completed_sentence for r in results)
        self.assertTrue(shakespeare_found)

        # Test case insensitive
        results = acs.get_best_k_completions("HELLO")
        hello_found = any("Hello world" in r.completed_sentence for r in results)
        self.assertTrue(hello_found)

    def test_file_filtering(self):
        """Test only .txt files are processed"""
        # Add non-txt file
        with open(os.path.join(self.test_dir, "ignore.csv"), 'w') as f:
            f.write("CSV,data,here\n")

        acs = AutoCompleteSystem()
        acs.build_from_folder(self.test_dir)

        # Should not find CSV content
        csv_found = any("CSV" in sentence for sentence, _, _ in acs.sentences)
        self.assertFalse(csv_found, "CSV files should be ignored")

    def test_subfolder_scanning(self):
        """Test recursive folder scanning"""
        # Create subfolder with content
        os.makedirs(os.path.join(self.test_dir, "subfolder"))
        with open(os.path.join(self.test_dir, "subfolder", "nested.txt"), 'w') as f:
            f.write("Nested file content\n")

        acs = AutoCompleteSystem()
        acs.build_from_folder(self.test_dir)

        # Should find nested content
        nested_found = any("Nested file" in sentence for sentence, _, _ in acs.sentences)
        self.assertTrue(nested_found, "Should find files in subfolders")


if __name__ == '__main__':
    unittest.main(verbosity=2)