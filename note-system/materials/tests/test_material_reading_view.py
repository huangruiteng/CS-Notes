import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from material_reading_view import merge_annotated_rows, normalize_projection_source_links


class ReadingViewTests(unittest.TestCase):
    def test_local_guide_keeps_source_and_reading_status_without_http_url(self):
        entries = [{'materials': [{'material_ref': 'guide',
            'primary_url': './payment-mechanisms/跨境数字支付机制导读.md',
            'source_status': 'Imported reviewed card, not reread.'}]}]
        result = normalize_projection_source_links(entries)
        material = result[0]['materials'][0]
        self.assertIsNone(material['primary_url'])
        self.assertIn('Learning-Materials/payment-mechanisms/跨境数字支付机制导读.md',
                      material['source_status'])
        self.assertIn('not reread', material['source_status'])
        self.assertEqual(material['material_ref'], 'guide')
        self.assertTrue(entries[0]['materials'][0]['primary_url'].startswith('./'))
        self.assertEqual(normalize_projection_source_links(result), result)

    def test_http_and_missing_sources_are_unchanged(self):
        entries = [{'materials': [{'primary_url': 'https://example.org/paper'},
                                   {'primary_url': 'https://docs.example.internal/page#section'},
                                   {'primary_url': None}]}]
        self.assertEqual(normalize_projection_source_links(entries), entries)

    def test_local_projection_keeps_public_source_boundary(self):
        for source in ['./payment-mechanisms/%2e%2e/private.md',
                       './payment-mechanisms/guide.md?token=secret',
                       './.local/private.md', 'file:///tmp/private.md']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                normalize_projection_source_links([{'materials': [{'primary_url': source}]}])

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
