import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from material_reading_view import merge_annotated_rows


class ReadingViewTests(unittest.TestCase):
    def test_duplicate_display_labels_keep_both_annotations(self):
        text='Preamble\n| 1 | A5 · First | first annotation |\n| 2 | A5 · Second | second annotation |\nFooter\n'
        entries=[{'labels':[x]} for x in ['A5','S129','A5']]
        result=merge_annotated_rows(text,entries,lambda rank,e:f'| {rank} | S129 · New | new note |')
        self.assertEqual(result,'Preamble\n| 1 | A5 · First | first annotation |\n| 2 | S129 · New | new note |\n| 3 | A5 · Second | second annotation |\nFooter\n')

    def test_removal_or_reorder_is_not_guessed(self):
        text='| 1 | A5 · First | note |\n| 2 | S2 · Second | other |'
        for labels in [['S2'],['S2','A5']]:
            with self.assertRaisesRegex(ValueError,'semantic'):
                merge_annotated_rows(text,[{'labels':[x]} for x in labels],lambda *args:'')
