# CLion navigation from the kit
Use the companion CLion-support branch in both repositories. The decomp's `tools/ide_compdb.py` owns the project model; the kit forwards to it instead of maintaining another set of compiler flags or changing candidate sources.
## Generate and open
Install LLVM/Clang, select its `clang`/`clang++` toolchain in CLion, and run from the kit:
```console
python clion.py jpn
```
`kitpaths.REPO` selects the decomp checkout (`DQIX_REPO`, otherwise `../dqix-decomp`). Open that checkout's generated `compile_commands.json` as a project in CLion and select the LLVM toolchain under **Settings > Build, Execution, Deployment > Compilation Database**. The file contains absolute paths, the 32-bit ARM target and the selected region's macros. Use `Ctrl+B` for declaration/definition navigation and `Alt+F7` for Find Usages.
For Clang outside `PATH`:
```console
python clion.py jpn --compiler "C:/Program Files/LLVM/bin/clang.exe"
```
No ROM, BIOS, prior build or CodeWarrior installation is needed to generate the database. `clion.py` does not run the matching pipeline or modify `build.ninja`. Without a region argument it uses `DQIX_REGION`, defaulting to `usa`.
## Include a candidate
Add only the work-in-progress files currently being edited, using their real paths:
```console
python clion.py jpn --source ../dqix-kit-state/wip/ov017/example.cpp
```
Repeat `--source` for more files. For a candidate built as a library, add `--build sdk`, `--build runtime`, or another family supported by the decomp. The family applies only to external candidates; tracked sources retain their actual settings. Including several alternate definitions of the same function can make navigation ambiguous. The kit's Python scripts themselves use CLion's Python support; they are not C/C++ compilation units.
Regenerate and reload the database (`Ctrl+Shift+O`) when changing region, sources or paths. Generation replaces the database, so include the wanted candidates each time. `--source` paths are resolved relative to the invoking directory before entering the decomp checkout.
## Limitations
This enables C/C++ code analysis, not a host port or a replacement compiler. Read `docs/CLION.md` in the decomp checkout for the compatibility header, build-family overrides and remaining CodeWarrior inline-assembly limitations. Clang uses C++11 only to parse CodeWarrior's extended union declarations; the real compiler's language rules are unchanged. Symbols defined only in assembly, linker configs or ROM do not become C/C++ definitions. Keep using `wgate.py`, `wdiff.py`, Ninja and objdiff for matching; CLion's syntax-only Recompile is not a matching check.
