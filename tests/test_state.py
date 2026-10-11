import unittest

from state import State, command_state


class CommandStateTests(unittest.TestCase):
    def test_recognized_activation_variants_allow_launch(self):
        for transcript in (
            "Kestrel, open Chrome",
            "Castrol launch Notepad",
            "Castor, open Visual Studio Code",
        ):
            with self.subTest(transcript=transcript):
                self.assertEqual(command_state(transcript), State.launch)

    def test_exit_requires_activation_word(self):
        self.assertEqual(command_state("Kestrel exit"), State.exit)
        self.assertEqual(command_state("exit"), State.default)

    def test_transcript_without_activation_stays_idle(self):
        self.assertEqual(command_state("please open Chrome"), State.default)

    def test_activation_without_supported_action_stays_idle(self):
        self.assertEqual(command_state("Kestrel how are you"), State.default)


if __name__ == "__main__":
    unittest.main()
