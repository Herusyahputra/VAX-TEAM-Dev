"""Fix emoji charmap error — ganti emoji di ai_service.py dengan ASCII-safe text"""
import re

path = r"f:\projek AI\VAX DEV v.1.2\app\services\ai_service.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = [
    # Progress bar dengan emoji blast rocket + block chars
    (
        lambda c: re.sub(
            r"print\(f\"\\r.{1,5} \[ENGINE PROGRESS\] \{job_id\}: \{p\}% \{'.' \* \(p // 5\)\}\{'.' \* \(20 - p // 5\)\}\", end=\"\", flush=True\)",
            'print(f"\\r[PROGRESS] {job_id}: {p}% |{\'#\' * (p // 5)}{\'-\' * (20 - p // 5)}|\", end="", flush=True)',
            c
        )
    ),
    # [JOB DONE]
    (
        lambda c: c.replace(
            '\u2705 [JOB DONE]',
            '[DONE]'
        )
    ),
    # [JOB FAILED]
    (
        lambda c: c.replace(
            '\u274c [JOB FAILED]',
            '[FAILED]'
        )
    ),
    # Download emoji
    (
        lambda c: c.replace('\U0001f4e5 [DOWNLOAD]', '[DOWNLOAD]')
    ),
]

original = content
for fn in replacements:
    content = fn(content)

# Fallback: replace ANY remaining non-ascii emoji ranges
import unicodedata

def strip_emoji(text):
    lines = []
    for line in text.splitlines(keepends=True):
        new_line = ""
        for ch in line:
            cp = ord(ch)
            # Emoji ranges: emoticons, symbols, etc.
            if (0x1F300 <= cp <= 0x1FFFF) or (0x2600 <= cp <= 0x27BF) or (0x2702 <= cp <= 0x27B0):
                # Skip emoji characters in print statements only
                pass
            else:
                new_line += ch
        lines.append(new_line)
    return "".join(lines)

# Only strip emoji inside print() calls
def strip_emoji_in_prints(text):
    result = []
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("print("):
            new_line = ""
            for ch in line:
                cp = ord(ch)
                if (0x1F300 <= cp <= 0x1FFFF) or (0x2600 <= cp <= 0x27BF) or ch in '\u2705\u274c\u2588\u2591\U0001f680\U0001f4e5':
                    pass  # drop emoji from print lines
                else:
                    new_line += ch
            result.append(new_line)
        else:
            result.append(line)
    return "".join(result)

content = strip_emoji_in_prints(content)

if content != original:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[OK] ai_service.py - emoji dihapus dari print statements")
else:
    print("[OK] Tidak ada perubahan - file sudah ASCII-safe")
