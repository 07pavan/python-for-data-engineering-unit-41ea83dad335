import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from milk_note import build_frame, load_records, main, summarise

SAMPLE = [
    {"farm": "Oakhill", "litres": 120.5, "fat_percent": 4.1},
    {"farm": "Meadowbrook", "litres": 80.0, "fat_percent": 3.9},
]


def run_main(path):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = main(["milk_note.py", path])
    return code, buffer.getvalue()


class MilkNoteTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def write_file(self, name, text):
        path = os.path.join(self.folder.name, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_build_frame_has_one_row_per_farm(self):
        df = build_frame(SAMPLE)
        self.assertEqual(list(df.columns), ["farm", "litres", "fat_percent"])
        self.assertEqual(list(df["farm"]), ["Oakhill", "Meadowbrook"])

    def test_build_frame_keeps_columns_when_empty(self):
        df = build_frame([])
        self.assertEqual(list(df.columns), ["farm", "litres", "fat_percent"])
        self.assertEqual(len(df), 0)

    def test_summarise_example_from_task(self):
        total, average_fat = summarise(build_frame(SAMPLE))
        self.assertEqual(total, 200.5)
        self.assertEqual(average_fat, 4.0)

    def test_summarise_rounds_average_to_two_places(self):
        records = [
            {"farm": "A", "litres": 10.0, "fat_percent": 4.0},
            {"farm": "B", "litres": 10.0, "fat_percent": 4.0},
            {"farm": "C", "litres": 10.0, "fat_percent": 4.1},
        ]
        total, average_fat = summarise(build_frame(records))
        self.assertEqual(total, 30.0)
        self.assertEqual(average_fat, 4.03)

    def test_total_hides_float_noise(self):
        records = [
            {"farm": "A", "litres": 0.1, "fat_percent": 4.0},
            {"farm": "B", "litres": 0.2, "fat_percent": 4.0},
        ]
        total, _ = summarise(build_frame(records))
        self.assertEqual(str(total), "0.3")

    def test_load_records_reads_utf8_names(self):
        path = self.write_file("in.json", '[{"farm": "Bryn Ŵy", "litres": 5, "fat_percent": 4}]')
        self.assertEqual(load_records(path)[0]["farm"], "Bryn Ŵy")

    def test_main_prints_table_and_note(self):
        path = self.write_file("in.json", '[{"farm": "Oakhill", "litres": 120.5, "fat_percent": 4.1},\r\n'
                                          ' {"farm": "Meadowbrook", "litres": 80.0, "fat_percent": 3.9}]\r\n')
        code, out = run_main(path)
        self.assertEqual(code, 0)
        self.assertIn("Oakhill", out)
        self.assertIn("Meadowbrook", out)
        self.assertTrue(out.endswith("Total litres: 200.5\nAverage fat: 4.00\n"))

    def test_main_missing_file(self):
        path = os.path.join(self.folder.name, "nope.json")
        code, out = run_main(path)
        self.assertEqual(code, 1)
        self.assertEqual(out, f"Error: file not found: {path}\n")

    def test_main_malformed_json(self):
        path = self.write_file("bad.json", '[{"farm": "Oakhill", "litres": 120.5,')
        code, out = run_main(path)
        self.assertEqual(code, 1)
        self.assertEqual(out, f"Error: {path} is not valid JSON\n")
        self.assertNotIn("Traceback", out)

    def test_main_without_argument_shows_usage(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(["milk_note.py"])
        self.assertEqual(code, 1)
        self.assertIn("Usage:", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()

