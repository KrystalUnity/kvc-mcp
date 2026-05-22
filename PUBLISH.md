# Publishing kvc-mcp

Publishing is operator-only.

1. `cd packages/kvc-mcp && uv build`
2. `uv publish --username __token__ --password "$PYPI_TOKEN"`
3. After PyPI has `kvc-mcp`, submit to the MCP Registry:
   - registry name: `io.github.KrystalUnity/kvc-mcp`
   - package: PyPI `kvc-mcp`
   - source: `https://github.com/KrystalUnity/kvc-mcp`
4. Verify in a fresh venv:

```bash
pip install kvc-mcp
kvc-mcp --help
```
