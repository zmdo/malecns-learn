import importlib
import sys

print("python", sys.version.split()[0], "|", sys.executable)
for m in ["numpy", "pandas", "scipy", "requests", "pyarrow", "neuprint", "matplotlib"]:
    try:
        mod = importlib.import_module(m)
        print("  {:12} OK  {}".format(m, getattr(mod, "__version__", "")))
    except Exception as e:
        print("  {:12} 缺  {}".format(m, type(e).__name__))
