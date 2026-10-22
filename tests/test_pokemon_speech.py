import json
import os
from pathlib import Path
import unittest

os.environ['ORT_DISABLE_TELEMETRY']='1'
from kokoro_onnx.tokenizer import Tokenizer
from shorts.pokemon_speech import lexicon, phonemes_for_text, speech_plan


class SpeechTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer=Tokenizer()
        cls.rules=lexicon()

    def test_catalogue_names_have_supported_explicit_phonemes(self):
        names={b['species'] for b in json.loads(Path('pokemon/builds.json').read_text())}
        self.assertEqual(names,set(self.rules['names']))
        for name,ipa in {**self.rules['names'],**self.rules['terms']}.items():
            with self.subTest(name=name):
                self.assertFalse(set(ipa)-set(self.tokenizer.vocab))
                self.assertEqual(phonemes_for_text(name,self.tokenizer,self.rules),ipa)

    def test_possessives_are_not_read_as_separate_letters(self):
        char=phonemes_for_text("Charizard's Life Orb",self.tokenizer,self.rules)
        blast=phonemes_for_text("Blastoise's Assault Vest",self.tokenizer,self.rules)
        self.assertIn(self.rules['names']['Charizard']+'z',char)
        self.assertIn(self.rules['names']['Blastoise']+'ɪz',blast)

    def test_item_and_move_pauses_preserve_complete_script(self):
        text='Charizard carries Life Orb. Blastoise uses Hydro Pump, removing health.'
        parts=speech_plan(text,self.rules)
        self.assertEqual(' '.join(p['text'] for p in parts),text)
        self.assertEqual(parts[0]['text'],'Charizard carries Life Orb.')
        self.assertEqual(parts[0]['pause_after'],.35)
        self.assertEqual(parts[1]['text'],'Blastoise uses Hydro Pump,')
        self.assertEqual(parts[1]['pause_after'],.35)

    def test_ordinary_narration_still_uses_normal_phonemization(self):
        sentence='The battle can change.'
        self.assertEqual(phonemes_for_text(sentence,self.tokenizer,self.rules),
                         self.tokenizer.phonemize(sentence,'en-us'))


if __name__=='__main__':
    unittest.main()
