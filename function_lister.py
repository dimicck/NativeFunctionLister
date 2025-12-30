import os
from typing import List, Optional, Set

from elftools.elf.elffile import ELFFile

def _extract_name(name: str) -> str:
    """
    Strip GNU symbol version suffixes.
    """
    return name.split("@", 1)[0]

def _is_exported_func(sym) -> bool:
    """
      Check if ELF symbol represents an exported, callable function.
      - Defined in this binary (not imported / SHN_UNDEF)
      - Function symbol (STT_FUNC)
      - Globally visible or weak
      - Visible to the dynamic loader (DEFAULT or PROTECTED)
      """
    return (
        sym["st_shndx"] != "SHN_UNDEF"
        and sym["st_info"]["type"] == "STT_FUNC"
        and sym["st_info"]["bind"] in ("STB_GLOBAL", "STB_WEAK")
        and sym["st_other"]["visibility"] in ("STV_DEFAULT", "STV_PROTECTED")
    )

def list_native_functions(file_path: str) -> List[str]:
    """
    Return a sorted list of exported native function names from a Linux .so file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    functions: Set[str] = set()


    # Parse the ELF binary, reflects runtime symbol availability
    with open(file_path, "rb") as f:
        elf = ELFFile(f)

        # Get symbols available to the dynamic loader
        sec = elf.get_section_by_name(".dynsym")
        if sec is None:
            return []

        for sym in sec.iter_symbols():
            if not _is_exported_func(sym):
                continue

            # Normalize the symbol name
            name = _extract_name(sym.name or "")

            # Keep only unmangled names - C and C++ functions exported with extern "C"
            if not name or name.startswith("_Z"):
                continue

            functions.add(name)

    return sorted(functions)

def main(argv: Optional[List[str]] = None) -> int:
    """
    Command-line entry point.

    Prints exported function names.
    Returns:
        0 on success
        2 on error
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="List exported native functions from a Linux shared object (.so)"
    )

    parser.add_argument("so", help="Path to .so file")
    args = parser.parse_args(argv)

    try:
        for fn in list_native_functions(args.so):
            print(fn)
        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())