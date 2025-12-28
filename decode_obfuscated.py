import base64
import zlib

# Read the obfuscated file
with open('secure_freeshipping_ultra.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the hex string
import re
match = re.search(r'self\.vrCYrtTq = "([^"]+)"', content)
if match:
    data = match.group(1)
    step1 = data[::-1]
    step2 = bytes.fromhex(step1)
    step3 = base64.b64decode(step2)
    step4 = zlib.decompress(step3)
    code = step4.decode('utf-8')
    print("=== secure_confirm_ultra.py decoded ===")
    print(code)
else:
    print("Pattern not found")
