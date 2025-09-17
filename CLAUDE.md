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

## Git Release Workflow Process

**CRITICAL**: Always follow this sequence when creating new releases:

### ✅ CORRECT Release Process:
```bash
# 1. Make code changes and commit
git add .
git commit -m "Your changes"

# 2. ALWAYS pull before push (automated workflow creates conflicts)
git pull origin main

# 3. Push changes
git push origin main

# 4. Create and push tag (if not already exists)
git tag v4.x.x
git push origin v4.x.x
```

### 🔍 Why `git pull` is needed:
- **Automated release workflow** triggers on tags
- **Workflow commits** ZIP files and updates repository files
- **Race condition** causes conflicts if we don't pull first
- **Pattern happens** on every version release

### ❌ WRONG - Will cause "failed to push" errors:
```bash
git commit -m "Changes"
git push origin main  # ERROR: Updates were rejected
```

## Common Issues

1. **YAML multiline Python** - Always use single quotes
2. **ZIP path checking** - Use correct path `service.cloudsync/service.cloudsync-VERSION.zip`
3. **addons.xml not updating** - Ensure workflow has step to update version in addons.xml
4. **Git push rejection** - Always `git pull origin main` before pushing
5. **Tag already exists** - Check if automated workflow already created the tag