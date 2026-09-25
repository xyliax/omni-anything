"""Build non-looping speech streams from the official LibriSpeech dev-clean archive.

Utterances from each speaker are concatenated in lexical order, with no silence
insertion or resampling. This is recorded read speech used as a systems input,
not a natural multi-turn conversational-quality evaluation.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import tarfile
import wave
from pathlib import Path

from infra.run.artifacts import sha256_file


DEV_CLEAN_MD5 = '42e2234ba48799c1f50f24a7926300a1'


def build(archive, output, *, speakers=8, minimum_seconds=180):
    import numpy as np
    import soundfile as sf
    archive, output = Path(archive), Path(output)
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream, 'md5').hexdigest() != DEV_CLEAN_MD5:
            raise ValueError('archive differs from the official dev-clean checksum')
    output.mkdir(parents=True, exist_ok=False)
    sources = {}
    with tarfile.open(archive, 'r:gz') as tar:
        members = sorted((m for m in tar.getmembers() if m.isfile() and m.name.endswith('.flac')), key=lambda m: m.name)
        grouped = {}
        for member in members:
            grouped.setdefault(Path(member.name).parts[-3], []).append(member)
        for speaker, clips in grouped.items():
            audio, pieces, total = [], [], 0
            for member in clips:
                raw = tar.extractfile(member).read()
                samples, rate = sf.read(io.BytesIO(raw), dtype='int16')
                if rate != 16000 or samples.ndim != 1:
                    raise ValueError('unexpected source audio format')
                pieces.append(dict(path=member.name, sha256=hashlib.sha256(raw).hexdigest(), samples=len(samples)))
                audio.append(samples)
                total += len(samples)
                if total >= minimum_seconds * 16000:
                    break
            if total < minimum_seconds * 16000:
                continue
            target = output / f'speaker-{speaker}.wav'
            with wave.open(str(target), 'wb') as stream:
                stream.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                stream.writeframes(np.concatenate(audio).astype('<i2', copy=False).tobytes())
            sources[target.name] = dict(sha256=sha256_file(target), samples=total, pieces=pieces)
            if len(sources) >= speakers:
                break
    if len(sources) != speakers:
        raise ValueError('not enough speakers with the requested continuous duration')
    result = dict(schema_version=1, dataset='LibriSpeech dev-clean',
        source='https://www.openslr.org/12', license='CC BY 4.0',
        archive_sha256=sha256_file(archive), archive_md5=DEV_CLEAN_MD5,
        transform='concatenate same-speaker utterances in lexical order without padding or looping', sources=sources)
    (output / 'provenance.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--speakers', type=int, default=8)
    parser.add_argument('--minimum-seconds', type=float, default=180)
    args = parser.parse_args()
    if args.speakers < 1 or args.minimum_seconds <= 0:
        parser.error('positive speaker count and duration required')
    build(args.archive, args.output, speakers=args.speakers, minimum_seconds=args.minimum_seconds)


if __name__ == '__main__':
    main()
