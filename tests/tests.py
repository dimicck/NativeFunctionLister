import os
import shutil
import subprocess
import tempfile
import unittest

from function_lister import list_native_functions
from elftools.common.exceptions import ELFError

C_SOURCE = r"""
#include <stdio.h>

int c_add(int a, int b) { return a + b; }
void c_hello(void) { puts("hello"); }

static int c_static(int x) { return x * 2; }  // static function
int global_var = 42;                          // data symbol
"""

CPP_SOURCE = r"""
#include <cstdio>

extern "C" int cpp_mul(int a, int b) { return a * b; }  // unmangled

int cpp_hidden(int x) { return x + 1; }                  // mangled
"""

# ----------------------------
# Helper utilities
# ----------------------------

def _have_tool(name: str) -> bool:
    """
    Check whether a compiler tool (gcc/g++) is available in PATH.

    Tests that require native compilation are skipped if the tool
    is not present in the environment.
    """
    return shutil.which(name) is not None


def _build_shared_objects(src: str, file_name: str, compiler: str) -> None:
    """
    Build a temporary shared library (.so) from provided C/C++ source for running tests.
    """
    src_path = file_name + (".c" if compiler == "gcc" else ".cpp")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write(src)


    # Compile a shared object suitable for dynamic loading
    cmd = [compiler, "-fPIC", "-shared", "-O0", "-o", file_name, src_path]
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)


class TestSoFunctions(unittest.TestCase):
    @unittest.skipUnless(_have_tool("gcc"), "gcc not available")
    def test_c_exports_only(self):
        """
        Verify that only exported C functions are listed.
        """
        with tempfile.TemporaryDirectory() as d:
            file_path = os.path.join(d, "libctest.so")
            _build_shared_objects(C_SOURCE, file_path, "gcc")

            functions = list_native_functions(file_path)
            self.assertEqual(functions, ["c_add", "c_hello"])

    @unittest.skipUnless(_have_tool("gcc"), "gcc not available")
    def test_imported_symbols_not_listed(self):
        """
        Verify that imported symbols don't appear in the result.
        """
        with tempfile.TemporaryDirectory() as d:
            so_path = os.path.join(d, "libimports.so")
            _build_shared_objects(C_SOURCE, so_path, "gcc")
            funcs = list_native_functions(so_path)

            self.assertNotIn("puts", funcs)

    @unittest.skipUnless(_have_tool("g++"), "g++ not available")
    def test_cpp_extern_mangled_excluded(self):
        """
        Verify that only C++ functions exported with extern "C" are listed.
        """
        with tempfile.TemporaryDirectory() as d:
            so_path = os.path.join(d, "libcpptest.so")
            _build_shared_objects(CPP_SOURCE, so_path, "g++")

            functions = list_native_functions(so_path)
            self.assertEqual(functions, ["cpp_mul"])

    def test_missing_file_raises(self):
        """
        A missing input file should raise FileNotFoundError.
        """
        with self.assertRaises(FileNotFoundError):
            list_native_functions("/no/such/file.so")

    def test_invalid_elf_raises(self):
        """
        A file that is not a valid ELF shared object should fail.
        """
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "not_valid.so")
            with open(p, "wb") as f:
                f.write(b"not an elf")

            with self.assertRaises(ELFError):
                list_native_functions(p)


if __name__ == "__main__":
    unittest.main(verbosity=2)
