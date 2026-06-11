import os
import sys
import importlib
import ast
from pathlib import Path
import traceback
import inspect

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def print_result(step, status, message=""):
    color = "\033[92m" if status == "PASS" else "\033[91m" if status == "FAIL" else "\033[93m"
    end = "\033[0m"
    print(f"{color}[{status}]{end} {step} {message}")

def check_backend_startup():
    try:
        from backend.main import app
        print_result("Backend Startup", "PASS")
    except Exception as e:
        print_result("Backend Startup", "FAIL", f"\n{traceback.format_exc()}")

def check_graph_compilation():
    try:
        from workflows.startup_graph import create_graph
        graph = create_graph()
        compiled = graph.compile()
        print_result("Graph Compilation", "PASS")
    except Exception as e:
        print_result("Graph Compilation", "FAIL", f"\n{traceback.format_exc()}")

def check_wiki_loading():
    try:
        from knowledge_wiki.compiler import KnowledgeCompiler
        print_result("Knowledge Wiki Loading", "PASS")
    except Exception as e:
        print_result("Knowledge Wiki Loading", "FAIL", f"\n{traceback.format_exc()}")

def check_research_platform():
    try:
        # Check if research platform can be imported
        import research_platform
        print_result("Research Platform Init", "PASS")
    except Exception as e:
        print_result("Research Platform Init", "FAIL", f"\n{traceback.format_exc()}")

def analyze_streamlit_pages():
    pages_dir = Path("frontend/pages")
    app_py = Path("frontend/app.py")
    files_to_check = [app_py]
    if pages_dir.exists():
        files_to_check.extend(list(pages_dir.glob("*.py")))

    for py_file in files_to_check:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
            
            # Check for missing unsafe_allow_html in st.markdown
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr == "markdown":
                        # Check if it has unsafe_allow_html=True
                        has_unsafe = False
                        for kw in node.keywords:
                            if kw.arg == "unsafe_allow_html" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                has_unsafe = True
                        
                        # If args contain <style> but no unsafe_allow_html, it's a bug
                        if not has_unsafe and node.args and isinstance(node.args[0], ast.Constant):
                            if "<style>" in str(node.args[0].value):
                                print_result(f"Streamlit CSS ({py_file.name})", "FAIL", "Missing unsafe_allow_html=True in st.markdown")
                                
                    elif node.func.attr == "rerun":
                        # Check for st.rerun outside of conditionals
                        print_result(f"Streamlit Rerun ({py_file.name})", "WARN", "st.rerun() detected. Check for recursive loops.")

        except Exception as e:
            print_result(f"Streamlit parsing ({py_file.name})", "FAIL", f"{e}")

def main():
    print("Running Diagnostics...\n")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    
    check_backend_startup()
    check_graph_compilation()
    check_wiki_loading()
    check_research_platform()
    analyze_streamlit_pages()

if __name__ == "__main__":
    main()
