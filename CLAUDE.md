# Claude Development Notes

## YAML Workflow Syntax Rules

**CRITICAL**: When editing `.github/workflows/release.yml`, NEVER use multiline Python code with double quotes!

### ❌ WRONG - Causes YAML syntax errors:
```yaml
run: |
  python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('file.xml')
"
```

### ✅ CORRECT - Use single quotes for Python code:
```yaml
run: |
  python3 -c '
import xml.etree.ElementTree as ET
tree = ET.parse("file.xml")
'
```

### ✅ BETTER - Use separate script file:
```yaml
run: |
  python3 scripts/update_xml.py
```

### ✅ BEST - Use simple one-liner:
```yaml
run: |
  sed -i 's/version="[^"]*"/version="${{ steps.get_version.outputs.VERSION }}"/' addons.xml
```

## Project Structure Notes

- ZIP files are created in `service.cloudsync/` directory
- Workflow checks for existing ZIP at `service.cloudsync/service.cloudsync-${VERSION}.zip`
- Repository files need to be updated: `addons.xml`, `addons.xml.md5`, `repository.cloudsync/`

## Common Issues

1. **YAML multiline Python** - Always use single quotes
2. **ZIP path checking** - Use correct path `service.cloudsync/service.cloudsync-VERSION.zip`
3. **addons.xml not updating** - Ensure workflow has step to update version in addons.xml