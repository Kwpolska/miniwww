#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Mini WWW Generator
# Copyright © 2017, Chris Warrick.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the author of this software nor the names of
#    contributors to this software may be used to endorse or promote
#    products derived from this software without specific prior written
#    consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""A small generator for even smaller webpages."""

import re
import typing
from pathlib import Path

ASSET_PATH = Path('assets/')
INPUT_PATH = Path('input/')
OUTPUT_PATH = Path('output/')

HtmlTemplate = typing.NewType("HtmlTemplate", str)
Html = typing.NewType("Html", str)
MetaDict = typing.NewType("MetaDict", typing.Dict[str, str])
PartType = typing.Union[HtmlTemplate, MetaDict]
PartDict = typing.Dict[str, PartType]

# Make sure all directories exist.
for d in (ASSET_PATH, INPUT_PATH, OUTPUT_PATH):
    if not d.exists():
        d.mkdir()

# Read all assets in.
ASSETS: typing.Dict[str, str] = {
    'footer-copyright': 'copyright © 2009–2017 <a href="https://chriswarrick.com/contact/">Chris Warrick</a>',
    'footer-operation': 'a <a href="https://chriswarrick.com/contact/">Chris Warrick</a> operation'
}

for path in ASSET_PATH.iterdir():
    if path.name.startswith('.'):
        continue
    with open(path, 'r', encoding='utf-8') as fh:
        ASSETS[path.name] = fh.read().strip()

with open('template.html', 'r', encoding='utf-8') as fh:
    ASSETS['template.html'] = fh.read()


def render_page(meta: MetaDict, content: HtmlTemplate, footer: typing.Optional[HtmlTemplate]) -> Html:
    """Render a template to HTML."""
    context = {
        'page_title': meta['page_title'],
        'header_title': meta['header_title'],
        'logo_href': meta.get('logo_href', '/'),
        'base': meta.get('base', ''),
        'css_html': '',
        'content_html': content,
    }
    context['html_title'] = meta.get('html_title', f"{context['page_title']} | {context['header_title']}")
    style_embeds: typing.List[str] = []
    style_links: typing.List[str] = []
    if meta['style'] == 'embed':
        style_embeds.append(ASSETS['style.css'])
    else:
        style_links.append('style.css')
    extra_css = meta.get('extra_css', '').split()
    for e in extra_css:
        filename, mode = e.split('!')
        if mode == 'embed':
            path: Path = ASSET_PATH / filename
            with open(path, 'r', encoding='utf-8') as fh:
                style_embeds.append(fh.read().strip())
        else:
            style_links.append(filename)

    for url in style_links:
        context['css_html'] += f'<link rel="stylesheet" href="{context["base"] + url}">\n'
    if style_embeds:
        context['css_html'] += '<style>\n' + '\n'.join(style_embeds) + '\n</style>'
    context['css_html'] = context['css_html'].strip()

    if footer is not None:
        context['footer_html'] = footer
    elif meta['footer'].startswith('custom'):
        context['footer_html'] = meta['footer'][7:]  # custom!xxx
    else:
        context['footer_html'] = ASSETS['footer-' + meta['footer']]

    if '!' in meta['logo']:
        logo_style, logo_base = meta['logo'].split('!')
        context['logo_base'] = logo_base
    else:
        logo_style = meta['logo']
        context['logo_base'] = context['base']
    context['logo_img_html'] = ASSETS[f'logo-{logo_style}.html'].format(**context)

    return Html(ASSETS['template.html'].format(**context))


def extract_parts(raw_content: str) -> PartDict:
    """Extract parts of input file."""
    split_raw: typing.List[str] = re.split(r'^--- ', raw_content, flags=re.MULTILINE)
    parts: PartDict = {}
    for part in split_raw:
        if not part:
            continue
        name, data = part.split('\n', maxsplit=1)
        if name == 'meta':
            meta = {}
            for line in data.strip().split('\n'):
                k, v = line.split(': ', maxsplit=1)
                meta[k] = v
            parts[name] = MetaDict(meta)
        elif name in {'content', 'footer'}:
            parts[name] = HtmlTemplate(data.strip())
        else:
            raise ValueError(f"Unknown part {name}")
    return parts


def main() -> None:
    """Generate HTML files."""
    files: typing.List[Path] = [path for path in INPUT_PATH.iterdir() if not path.name.startswith('.')]
    size: int = len(files)
    sizesize: int = len(str(size))
    for num, path in enumerate(files, 1):
        print(f"({num:>{sizesize}}/{size:>{sizesize}}) {path.name}")
        with open(path, 'r', encoding='utf-8') as fh:
            parts: PartDict = extract_parts(fh.read())
        output: Html = render_page(meta=typing.cast(MetaDict, parts['meta']),
                                   content=typing.cast(HtmlTemplate, parts['content']),
                                   footer=typing.cast(HtmlTemplate, parts.get('footer')))
        output_path: Path = OUTPUT_PATH / path.relative_to(INPUT_PATH)
        with open(output_path, 'w', encoding='utf-8') as fh:
            fh.write(output)


if __name__ == '__main__':
    main()
