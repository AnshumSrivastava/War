
import sys

dependencies = [
    'PyQt5',
    'PyQt5.QtWebEngineWidgets',
    'numpy',
    'gymnasium',
    'pygame',
    'supabase'
]

missing = []

for dep in dependencies:
    try:
        __import__(dep)
        print(f"✅ {dep} is available")
    except ImportError as e:
        print(f"❌ {dep} is MISSING: {e}")
        missing.append(dep)

if not missing:
    print("\nAll dependencies are available!")
    sys.exit(0)
else:
    print(f"\nMissing {len(missing)} dependencies.")
    sys.exit(1)
