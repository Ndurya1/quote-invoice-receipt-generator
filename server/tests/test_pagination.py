import unittest

from app.common.pagination import validate_pagination


class PaginationTests(unittest.TestCase):
    def test_valid_values_produce_offset(self):
        pagination = validate_pagination(3, 25)
        self.assertEqual(pagination.offset, 50)

    def test_invalid_values_are_rejected(self):
        for page, page_size in ((0, 20), (1, 0), (2_147_483_648, 20), (1, 101)):
            with self.subTest(page=page, page_size=page_size):
                with self.assertRaises(ValueError):
                    validate_pagination(page, page_size)
