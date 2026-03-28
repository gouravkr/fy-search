import unittest

from PySide6.QtCore import Qt

from fy_search.ui import MultiSortProxyModel, ResultRow, SearchResultModel


class DateSortingTests(unittest.TestCase):
    def setUp(self):
        self.model = SearchResultModel()
        self.model._results = [
            ResultRow("oldest", "/tmp/oldest", False, 1, 100.0, 100.0),
            ResultRow("middle", "/tmp/middle", False, 1, 200.0, 200.0),
            ResultRow("newest", "/tmp/newest", False, 1, 300.0, 300.0),
        ]
        self.proxy = MultiSortProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setSortRole(Qt.ItemDataRole.EditRole)

    def _names_in_order(self):
        return [self.proxy.data(self.proxy.index(row, 0), Qt.ItemDataRole.DisplayRole) for row in range(self.proxy.rowCount())]

    def test_modified_on_sorts_ascending(self):
        self.proxy.sort(5, Qt.SortOrder.AscendingOrder)
        self.assertEqual(self._names_in_order(), ["oldest", "middle", "newest"])

    def test_modified_on_sorts_descending(self):
        self.proxy.sort(5, Qt.SortOrder.DescendingOrder)
        self.assertEqual(self._names_in_order(), ["newest", "middle", "oldest"])

    def test_created_on_sorts_descending(self):
        self.proxy.sort(4, Qt.SortOrder.DescendingOrder)
        self.assertEqual(self._names_in_order(), ["newest", "middle", "oldest"])

    def test_toggle_sort_column_flips_modified_on_order(self):
        self.proxy.toggle_sort_column(5)
        self.assertEqual(self._names_in_order(), ["oldest", "middle", "newest"])

        self.proxy.toggle_sort_column(5)
        self.assertEqual(self._names_in_order(), ["newest", "middle", "oldest"])
