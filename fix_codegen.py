with open('aima_codegen/agents/codegen.py', 'r') as f:
    content = f.read()

# Find the prompt string and escape the JSON examples
import re

# Find the JSON example in the prompt
pattern = r'(Example:\s*\n```json\s*\n)(.*?)(\n```)'
def escape_json(match):
    prefix = match.group(1)
    json_content = match.group(2)
    suffix = match.group(3)
    # Escape the braces in the JSON content
    escaped = json_content.replace('{', '{{').replace('}', '}}')
    return prefix + escaped + suffix

content = re.sub(pattern, escape_json, content, flags=re.DOTALL)

with open('aima_codegen/agents/codegen.py', 'w') as f:
    f.write(content)
print('Fixed JSON escaping in codegen.py')
