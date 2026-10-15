import unittest

from silent_type.icon import mark


class IconTests(unittest.TestCase):
    def test_states_draw_at_tray_and_shortcut_sizes(self):
        for size in (16, 32, 256):
            for state in ("ready", "recording", "working", "off"):
                image = mark(size, state)
                self.assertEqual(image.size, (size, size))
                self.assertIsNotNone(image.getbbox())

    def test_off_is_gray_and_recording_adds_a_green_dot(self):
        r, g, b, _ = mark(64, "off").getpixel((32, 32))
        self.assertTrue(r == g == b)
        corner = mark(64, "recording").getpixel((56, 56))
        self.assertEqual(corner[:3], (0x14, 0x78, 0x3D))


if __name__ == "__main__":
    unittest.main()
