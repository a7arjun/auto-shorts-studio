import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
from PIL import Image,ImageDraw
from shorts.pokemon_assets import PokeAPIImages,ImageSourceError,image_candidates,validate_image


class AssetTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.provider=PokeAPIImages(cache_root=self.directory.name)
        image=Image.new('RGBA',(40,40),(0,0,0,0));ImageDraw.Draw(image).rectangle((5,5,34,34),fill='red')
        data=io.BytesIO();image.save(data,format='PNG');self.image=data.getvalue()
        self.first='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-viii/brilliant-diamond-shining-pearl/icons/6.png'
        self.second='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ix/scarlet-violet/icons/6.png'
        self.metadata={'id':6,'name':'charizard','sprites':{'versions':{
            'generation-viii':{'brilliant-diamond-shining-pearl':{'icons':{'front_default':self.first}}},
            'generation-ix':{'scarlet-violet':{'icons':{'front_default':self.second}}}}}}

    def test_downloaded_character_survives_source_outage(self):
        self.provider.get=Mock(side_effect=lambda url,image=False:self.image if image else self.metadata)
        first=self.provider.resolve('Charizard')
        self.assertFalse(first['cache_hit']);self.assertEqual(first['pokemon_id'],6)
        self.provider.get=Mock(side_effect=ImageSourceError('offline'))
        second=self.provider.resolve('Charizard')
        self.assertTrue(second['cache_hit']);self.assertEqual(first['sha256'],second['sha256'])
        self.provider.get.assert_not_called()

    def test_missing_preferred_icon_uses_another_icon_for_same_pokemon(self):
        def get(url,image=False):
            if not image:return self.metadata
            if url==self.first:raise ImageSourceError('not found')
            return self.image
        self.provider.get=Mock(side_effect=get)
        result=self.provider.resolve('Charizard')
        self.assertEqual(result['style'],'sv-mini')
        self.assertEqual(result['source_url'],self.second)

    def test_cold_start_uses_bundled_url_snapshot_when_api_is_offline(self):
        snapshot=Path(self.directory.name)/'snapshot.json'
        snapshot.write_text(json.dumps({'entries':{'Charizard':self.metadata}}))
        def get(url,image=False):
            if not image:raise ImageSourceError('metadata API offline')
            return self.image
        self.provider.get=Mock(side_effect=get)
        with patch('shorts.pokemon_assets.SNAPSHOT_PATH',snapshot):
            result=self.provider.resolve('Charizard')
        self.assertEqual(result['metadata_origin'],'bundled-api-snapshot')
        self.assertEqual(result['pokemon_id'],6)

    def test_wrong_api_identity_stops_before_image_download(self):
        self.provider.get=Mock(return_value={**self.metadata,'name':'blastoise'})
        with self.assertRaisesRegex(ImageSourceError,'identity'):
            self.provider.resolve('Charizard')
        self.assertEqual(self.provider.get.call_count,1)

    def test_corrupted_cache_redownloads_using_cached_api_metadata(self):
        self.provider.get=Mock(side_effect=lambda url,image=False:self.image if image else self.metadata)
        record=self.provider.resolve('Charizard');Path(record['path']).write_bytes(b'corrupted')
        self.provider.get.reset_mock()
        self.provider.resolve('Charizard')
        self.assertEqual(self.provider.get.call_count,1)
        self.assertTrue(self.provider.get.call_args.kwargs['image'])

    def test_images_are_never_assumed_commercially_licensed(self):
        self.provider.get=Mock(side_effect=lambda url,image=False:self.image if image else self.metadata)
        record=self.provider.resolve('Charizard')
        self.assertEqual(record['rights_status'],'underlying_pokemon_rights_reserved')
        self.assertIn('do not establish a commercial artwork licence',record['usage_basis'])

    def test_invalid_bytes_rejected(self):
        for data in [b'',b'<html>Not an image</html>']:
            with self.assertRaises(ImageSourceError):validate_image(data)

    def test_untrusted_or_wrong_character_image_url_rejected(self):
        self.metadata['sprites']['versions']['generation-viii']['brilliant-diamond-shining-pearl']['icons']['front_default']='http://127.0.0.1/private.png'
        self.metadata['sprites']['versions']['generation-ix']['scarlet-violet']['icons']['front_default']=self.second.replace('/6.png','/9.png')
        self.assertEqual(list(image_candidates(self.metadata)),[])


if __name__=='__main__':
    unittest.main()
