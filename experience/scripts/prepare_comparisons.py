"""Prepare supplied comparison assets without modifying the Downloads originals.

Requires Pillow, libarchive (for RAR) and Blender 4.3+ with its glTF exporter.
Run: python scripts/prepare_comparisons.py --downloads ~/Downloads --blender /path/to/blender
"""
import argparse
import ctypes
import ctypes.util
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from PIL import Image


def extract_rar(source, destination):
    lib = ctypes.CDLL(ctypes.util.find_library('archive'))
    signatures = {
        'archive_read_new': (ctypes.c_void_p, []),
        'archive_read_support_format_all': (ctypes.c_int, [ctypes.c_void_p]),
        'archive_read_support_filter_all': (ctypes.c_int, [ctypes.c_void_p]),
        'archive_read_open_filename': (ctypes.c_int, [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]),
        'archive_read_next_header': (ctypes.c_int, [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]),
        'archive_entry_pathname': (ctypes.c_char_p, [ctypes.c_void_p]),
        'archive_entry_filetype': (ctypes.c_int, [ctypes.c_void_p]),
        'archive_read_data': (ctypes.c_ssize_t, [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]),
        'archive_read_free': (ctypes.c_int, [ctypes.c_void_p]),
    }
    for name, (restype, argtypes) in signatures.items():
        fn = getattr(lib, name)
        fn.restype, fn.argtypes = restype, argtypes
    archive = lib.archive_read_new()
    try:
        lib.archive_read_support_format_all(archive)
        lib.archive_read_support_filter_all(archive)
        if lib.archive_read_open_filename(archive, str(source).encode(), 10240) != 0:
            raise RuntimeError(f'Cannot open {source}')
        entry, buffer = ctypes.c_void_p(), ctypes.create_string_buffer(1024 * 1024)
        while True:
            status = lib.archive_read_next_header(archive, ctypes.byref(entry))
            if status == 1:
                break
            if status != 0:
                raise RuntimeError(f'Cannot read {source}')
            if lib.archive_entry_filetype(entry) != 0o100000:
                continue
            # Flatten only regular files; never trust archive paths or symlinks.
            name = Path(lib.archive_entry_pathname(entry).decode()).name
            with (destination / name).open('wb') as output:
                while True:
                    count = lib.archive_read_data(archive, buffer, len(buffer))
                    if count == 0:
                        break
                    if count < 0:
                        raise RuntimeError(f'Cannot extract {name}')
                    output.write(buffer.raw[:count])
    finally:
        lib.archive_read_free(archive)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads', type=Path, default=Path.home() / 'Downloads')
    parser.add_argument('--blender', default='blender')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / 'public/models/comparisons'
    sources = ['Car+Skoda+Kodiaq+2016.obj', 'textures.rar', 'Ivan_1304.obj',
               'Ivan_1304_Textures.rar', 'Marina_1276.obj', 'Marina_1276_Textures.rar',
               'Modern+House_05_blend.zip', 'Modern+House_05_scanline_max.zip']
    hashes = {name: hashlib.sha256((args.downloads / name).read_bytes()).hexdigest() for name in sources}
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='comparison-assets-') as temporary:
        staging = Path(temporary)
        for name in sources:
            source = args.downloads / name
            if source.suffix == '.rar':
                extract_rar(source, staging)
            elif source.suffix == '.zip':
                with zipfile.ZipFile(source) as archive:
                    for member in archive.namelist():
                        if Path(member).suffix.lower() in ('.blend', '.jpg', '.png'):
                            (staging / Path(member).name).write_bytes(archive.read(member))
            else:
                shutil.copyfile(source, staging / name)
        # Keep detailed 2K colour atlases; normal maps need only 1K at this scale.
        # JPEG normals trade negligible shading error for much smaller downloads.
        for path in list(staging.iterdir()):
            if path.suffix.lower() not in ('.png', '.jpg'):
                continue
            with Image.open(path) as original:
                image = original.convert('RGB')
                limit = 2048 if '_DIFF' in path.name else 1024
                image.thumbnail((limit, limit), Image.Resampling.LANCZOS)
                image.save(staging / (path.stem + '-web.jpg'), quality=90, subsampling=0, optimize=True)
        textures = root / 'public/textures'
        textures.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(staging / 'Modern House_01_TEXTURE (4)-web.jpg', textures / 'concrete-aggregate.jpg')
        subprocess.run([args.blender, '-b', '-noaudio', '--factory-startup', '--python-exit-code', '1',
                        '--python', str(root / 'scripts/convert_comparisons_blender.py'),
                        '--', str(staging), str(output)], check=True, timeout=600)
    report_path = output / 'provenance.json'
    report = json.loads(report_path.read_text())
    report['source_sha256'] = hashes
    report['source_rights'] = 'User-supplied assets; original license documents were not included in these exports.'
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    # Finish with the newer 3DS house so a full rebuild cannot restore the old one.
    subprocess.run(['python', str(root / 'scripts/prepare_house_3ds.py'),
                    '--source', str(args.downloads / 'model_dom_2.3DS'),
                    '--textures', str(args.downloads / 'Modern+House_05_scanline_max.zip'),
                    '--blender', args.blender], check=True)
    report = json.loads(report_path.read_text())
    # Use Three.js's matching local decoder: no external CDN requests.
    decoder = root / 'public/decoders/draco'
    decoder.mkdir(parents=True, exist_ok=True)
    for name in ['draco_wasm_wrapper.js', 'draco_decoder.wasm']:
        shutil.copyfile(root / 'node_modules/three/examples/jsm/libs/draco/gltf' / name, decoder / name)
    shutil.copyfile(root / 'node_modules/three/examples/jsm/libs/draco/README.md', decoder / 'README.md')
    # Apache-2.0 LICENSE is committed alongside these vendored decoder files.
    print(json.dumps(report['assets'], indent=2))


if __name__ == '__main__':
    main()
