import unittest

from invoices.export import export
from invoices.models import Invoice


class ExportTest(unittest.TestCase):
    def test_one_row_per_invoice(self) -> None:
        text = export([Invoice("A1", "Ada", 1250)])
        self.assertEqual(text.splitlines()[1], "A1,Ada,1250")
