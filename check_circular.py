import os
import ast
import networkx as nx

# Path addons → pakai current directory
ADDONS_PATH = "."

def get_module_dependencies(module_path):
    """Baca file __manifest__.py dan ambil daftar depends"""
    manifest_path = os.path.join(module_path, "__manifest__.py")
    if not os.path.exists(manifest_path):
        return []

    with open(manifest_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        manifest = ast.literal_eval(content)
        return manifest.get("depends", [])
    except Exception as e:
        print(f"⚠️ Gagal parsing {manifest_path}: {e}")
        return []

def build_dependency_graph(addons_path):
    """Bangun graph dependency antar modul"""
    G = nx.DiGraph()
    modules = [m for m in os.listdir(addons_path) if os.path.isdir(os.path.join(addons_path, m))]

    for module in modules:
        deps = get_module_dependencies(os.path.join(addons_path, module))
        if module not in G:
            G.add_node(module)
        for dep in deps:
            G.add_edge(module, dep)  # arah: module → dependency
    return G

if __name__ == "__main__":
    G = build_dependency_graph(ADDONS_PATH)
    print(f"✅ Dependency graph dibuat dengan {len(G.nodes)} modul.")

    cycles = list(nx.simple_cycles(G))
    if not cycles:
        print("🎉 Tidak ada circular dependency ditemukan.")
    else:
        print("🔄 Circular dependencies:")
        for c in cycles:
            print("   - " + " -> ".join(c))
