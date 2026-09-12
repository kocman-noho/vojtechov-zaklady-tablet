"""Replace the browser house from model_dom_2.3DS without changing other models.

Requires Pillow and Blender with Draco export; run from any directory:
python scripts/prepare_house_3ds.py --blender /path/to/blender
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.home() / 'Downloads/model_dom_2.3DS')
    parser.add_argument('--textures', type=Path, default=Path.home() / 'Downloads/Modern+House_05_scanline_max.zip')
    parser.add_argument('--blender', default='blender')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / 'public/models/comparisons'
    with tempfile.TemporaryDirectory(prefix='house-3ds-') as directory:
        staging = Path(directory)
        subprocess.run(['node', str(root / 'scripts/read_house_3ds.mjs'), str(args.source.resolve()),
                        str(staging / 'house.glb'), str(staging / 'source.json')], check=True)
        # Supplement missing image maps using textures already supplied for this project.
        with zipfile.ZipFile(args.textures) as archive:
            for number, name in [(6, 'wood'), (2, 'stone')]:
                member = next(n for n in archive.namelist() if n.endswith(f'TEXTURE ({number}).jpg'))
                with archive.open(member) as image_file, Image.open(image_file) as image:
                    image = image.convert('RGB')
                    image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                    image.save(staging / f'{name}.jpg', quality=88, optimize=True)
        subprocess.run([args.blender, '-b', '-noaudio', '--factory-startup', '--python-exit-code', '1',
                        '--python', str(root / 'scripts/convert_house_3ds_blender.py'), '--',
                        str(staging), str(staging / 'house-browser.glb')], check=True, timeout=600)
        info = json.loads((staging / 'source.json').read_text())
        asset = json.loads((staging / 'output.json').read_text())
        asset.update(source_file=args.source.name, source_sha256=hashlib.sha256(args.source.read_bytes()).hexdigest(),
                     original_image_textures=False, original_materials=info['materials'],
                     excluded_site_meshes=info['excluded'], original_triangles=info['originalTriangles'],
                     retained_before_optimization=info['retainedTriangles'],
                     supplemental_textures={'archive': args.textures.name,
                                            'sha256': hashlib.sha256(args.textures.read_bytes()).hexdigest(),
                                            'wood': 'Modern House_01_TEXTURE (6).jpg',
                                            'stone': 'Modern House_01_TEXTURE (2).jpg'})
        output.mkdir(parents=True, exist_ok=True)
        (output / 'house.glb').write_bytes((staging / 'house-browser.glb').read_bytes())
        report_path = output / 'provenance.json'
        report = json.loads(report_path.read_text())
        report['assets']['house'] = asset
        report['processing'] = ('Car paint, glazing and lamps retain source topology; other car details simplified. '
                                'People retain scan geometry and 2K colour/1K normal maps. The replacement 3DS house '
                                'has named material regions but no source image maps; PBR finishes and supplied supplemental '
                                'wood/stone textures added. Site meshes excluded and curtains simplified; original roof tile geometry preserved. All models use Draco geometry.')
        report['source_sha256'][args.source.name] = asset['source_sha256']
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(asset, indent=2))


if __name__ == '__main__':
    main()
