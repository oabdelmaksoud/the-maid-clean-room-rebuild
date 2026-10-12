"""Bounded, dependency-free oracles for recorded journeys and RGB captures."""
import re

MAX_PIXELS = 1_000_000
MAX_DIMENSION = 4096
MAX_COMPARISON_PIXELS = 16_000_000
MAX_HEADER_BYTES = 128
# Deliberately narrow PPM subset: no comments, 8-bit RGB, one raster only.
PPM_HEADER = re.compile(rb'P6[ \t\r\n]+([0-9]{1,4})[ \t\r\n]+([0-9]{1,4})[ \t\r\n]+255(?:\r\n|[ \t\r\n])')


def journey(value, path):
    from core import array, fail, ident, shape, text
    shape(value, 'steps', path)
    array(value['steps'], path + '.steps')
    if not value['steps']:
        fail('JOURNEY_EMPTY', path, 'At least one recorded step required')
    seen = set()
    for i, step in enumerate(value['steps']):
        p = f'{path}.steps[{i}]'
        shape(step, 'id action state', p)
        ident(step['id'], p + '.id')
        text(step['action'], p + '.action')
        if step['id'] in seen:
            fail('JOURNEY_DUPLICATE', p, 'Step IDs must be unique')
        seen.add(step['id'])
        if not isinstance(step['state'], dict) or not step['state']:
            fail('JOURNEY_STATE', p, 'State must be a nonempty JSON object')


def pixels(raw, path):
    from core import fail, integer
    match = PPM_HEADER.match(raw[:MAX_HEADER_BYTES])
    if match is None:
        fail('VISUAL_FORMAT', path, 'Expected P6 width height 255 header without comments')
    width, height = (int(v) for v in match.groups())
    integer(width, 1, MAX_DIMENSION, path + '.width')
    integer(height, 1, MAX_DIMENSION, path + '.height')
    if width * height > MAX_PIXELS:
        fail('VISUAL_SIZE', path, f'Image exceeds {MAX_PIXELS} pixels')
    if len(raw) != match.end() + width * height * 3:
        fail('VISUAL_RASTER', path, 'RGB raster length must exactly match dimensions')
    return width, height, memoryview(raw)[match.end():]


def visual_expected(value, path, reader):
    from core import fail, integer, shape
    shape(value, 'baseline width height max_channel_delta max_changed_pixels', path)
    integer(value['width'], 1, MAX_DIMENSION, path + '.width')
    integer(value['height'], 1, MAX_DIMENSION, path + '.height')
    count = value['width'] * value['height']
    if count > MAX_PIXELS:
        fail('VISUAL_SIZE', path, f'Image exceeds {MAX_PIXELS} pixels')
    integer(value['max_channel_delta'], 0, 254, path + '.max_channel_delta')
    integer(value['max_changed_pixels'], 0, count - 1, path + '.max_changed_pixels')
    width, height, _ = pixels(reader.ref(value['baseline'], path + '.baseline'), path + '.baseline')
    if (width, height) != (value['width'], value['height']):
        fail('VISUAL_DIMENSIONS', path, 'Baseline dimensions differ from frozen contract')


def visual_matches(value, raw, path, reader):
    from core import fail
    width, height, actual = pixels(raw, path)
    if (width, height) != (value['width'], value['height']):
        return False
    reader.visual_pixels_checked += width * height
    if reader.visual_pixels_checked > MAX_COMPARISON_PIXELS:
        fail('VISUAL_BUDGET', path, f'Run exceeds {MAX_COMPARISON_PIXELS} comparison pixels')
    _, _, baseline = pixels(reader.ref(value['baseline'], path + '.baseline'), path + '.baseline')
    delta = value['max_channel_delta']
    changed = 0
    for offset in range(0, len(actual), 3):
        if any(abs(actual[offset + channel] - baseline[offset + channel]) > delta for channel in range(3)):
            changed += 1
            if changed > value['max_changed_pixels']:
                return False
    return True
