#!/usr/bin/env python3
"""모든 HTML 페이지에 GA4 태그를 심는다.

사용법:  python3 tools/inject_ga4.py G-XXXXXXXXXX
        python3 tools/inject_ga4.py --remove

애드센스 스크립트 바로 뒤에 넣는다(<head> 안, 이미 모든 페이지에 있는 유일한 공통 앵커).
여러 번 돌려도 안전하다 — 기존 블록이 있으면 지우고 다시 넣으므로 측정 ID 교체에도 그대로 쓴다.
지역 페이지를 다시 생성하면 태그가 사라지므로 생성 후 이 스크립트를 반드시 다시 돌릴 것.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ANCHOR = re.compile(
    r'^.*pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js.*$',
    re.MULTILINE,
)
BLOCK = re.compile(r'\n?<!-- GA4 start -->.*?<!-- GA4 end -->\n?', re.DOTALL)


def block(mid: str) -> str:
    return (
        '\n<!-- GA4 start -->\n'
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={mid}"></script>\n'
        '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
        f"gtag('js',new Date());gtag('config','{mid}');</script>\n"
        '<script defer src="/ga-events.js"></script>\n'
        '<!-- GA4 end -->'
    )


def pages():
    yield from sorted(ROOT.glob('*.html'))
    yield from sorted((ROOT / 'regions').glob('*.html'))
    yield from sorted((ROOT / 'maechul').glob('*.html'))


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    arg = sys.argv[1]
    remove = arg == '--remove'
    if not remove and not re.fullmatch(r'G-[A-Z0-9]{6,14}', arg):
        print(f'측정 ID 형식이 아닙니다: {arg}  (예: G-ABCD123456)')
        return 2

    changed = skipped = 0
    for p in pages():
        src = p.read_text(encoding='utf-8')
        out = BLOCK.sub('\n', src)
        if not remove:
            m = ANCHOR.search(out)
            if not m:
                print(f'  앵커 없음, 건너뜀: {p.relative_to(ROOT)}')
                skipped += 1
                continue
            out = out[: m.end()] + block(arg) + out[m.end():]
        if out != src:
            p.write_text(out, encoding='utf-8')
            changed += 1

    verb = '제거' if remove else '삽입'
    print(f'{verb} 완료: {changed}개 파일 수정, {skipped}개 건너뜀')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
