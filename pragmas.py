import re
from collections import Counter

CODEGEN_PRAGMA = re.compile(r"(?m)^[ \t]*#[ \t]*pragma[ \t]+(?!(?:define_section|section|once)\b)(\w+)")

_LITERALS = re.compile(
    r'R"(?P<delimiter>[^ ()\\\t\r\n]{0,16})\(.*?\)(?P=delimiter)"'
    r'|//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S)
_TOKENS = re.compile(r'\w+|[^\s]')


def _hide_literal(match):
    text = match.group()
    if text.startswith(('//', '/*')):
        return re.sub(r'[^\n]', ' ', text)
    return '__literal_' + text.encode('utf-8').hex() + '__' + '\n' * text.count('\n')


def _display(text):
    return re.sub(r'__literal_([0-9a-f]+)__',
                  lambda m: bytes.fromhex(m[1]).decode('utf-8'), text)


def _off_declarations(lines, opaque=False):
    depth, pending, declarations, tokens = 0, [], [], []
    def result():
        return tuple(declarations) + (('ambiguous scope: ' + ' '.join(tokens),) if opaque else ())
    for line in lines:
        directive = re.match(r'^\s*#\s*(\w+)\b(.*)', line)
        if directive:
            name, rest = directive.groups()
            if name == 'pragma' and re.match(r'\s*optimize_for_size\b', rest):
                break
            if name in ('if', 'ifdef', 'ifndef', 'elif', 'else', 'endif'):
                declarations.append(' '.join(_TOKENS.findall(line)))
            continue
        for token in _TOKENS.findall(line):
            tokens.append(token)
            if token == '{':
                if depth == 0:
                    header = ' '.join(pending)
                    opaque |= bool(re.search(r'\b(class|struct|union|namespace)\b', header))
                    declarations.append(header + ' {')
                    pending = []
                depth += 1
            elif token == '}':
                if depth == 0:
                    return result()
                depth -= 1
            elif depth == 0:
                pending.append(token)
                if token == ';':
                    declarations.append(' '.join(pending))
                    pending = []
    return result()


def _pragma_sites(source):
    source = re.sub(r'\\\r?\n', '', source)
    source = _LITERALS.sub(_hide_literal, source)
    lines = source.splitlines()
    scopes, pending, conditions, sites = [], [], [], []
    for number, line in enumerate(lines, 1):
        directive = re.match(r'^\s*#\s*(\w+)\b(.*)', line)
        if directive:
            name, rest = directive.groups()
            if name in ('if', 'ifdef', 'ifndef'):
                conditions.append(' '.join(_TOKENS.findall(name + rest)))
            elif name in ('elif', 'else') and conditions:
                conditions[-1] += ' / ' + ' '.join(_TOKENS.findall(name + rest))
            elif name == 'endif' and conditions:
                conditions.pop()
            if name == 'pragma' and CODEGEN_PRAGMA.match(line):
                following = []
                for tail in lines[number:]:
                    if re.match(r'^\s*#', tail):
                        continue
                    for token in _TOKENS.findall(tail):
                        following.append(token)
                        if token in ('{', '}', ';'):
                            break
                    if following and following[-1] in ('{', '}', ';'):
                        break
                text = ' '.join(_TOKENS.findall(rest))
                covered = (_off_declarations(lines[number:], opaque=bool(scopes))
                           if text == 'optimize_for_size off' else ())
                key = ((text, tuple(scopes), tuple(conditions), ' '.join(following), covered)
                       if text == 'optimize_for_size off' else (text, (), (), '', ()))
                sites.append((number, key))
            continue
        for token in _TOKENS.findall(line):
            if token == '{':
                scopes.append(' '.join(pending))
                pending = []
            elif token == '}':
                if scopes:
                    scopes.pop()
                pending = []
            elif token == ';':
                pending = []
            else:
                pending.append(token)
    return sites


def changed_codegen_pragmas(before, after):
    original = _pragma_sites(before)
    remaining = Counter(key for _, key in original)
    changed = []
    for number, key in _pragma_sites(after):
        if remaining[key]:
            remaining[key] -= 1
        else:
            def context(site):
                return (f'scope={_display(" / ".join(site[1])) or "top-level"}, '
                        f'guard={_display(" / ".join(site[2])) or "none"}, '
                        f'range={[_display(x)[:120] for x in site[4][:3]]} ({len(site[4])} entries)')
            previous = [f'line {line}: #pragma {old[0]} before {old[3] or "EOF"}; {context(old)}'
                        for line, old in original if old[0].split()[0] == key[0].split()[0]]
            changed.append(f'line {number}: #pragma {key[0]} before {key[3] or "EOF"} '
                           f'(added, changed, or application context changed); {context(key)}; previous: '
                           + ('; '.join(previous) or 'none')
                           + ('; nested/record scope needs exact-diff review'
                              if any(x.startswith('ambiguous scope:') for x in key[4]) else ''))
    return changed
