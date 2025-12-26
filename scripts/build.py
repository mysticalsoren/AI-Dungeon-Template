import os
import shutil
import json
import subprocess

def findSrc(directory: os.DirEntry) -> None | os.DirEntry:
    """
    Retrieves any src folder regardless of depth.
    ```python
    - library-A/
        - examples/
            - src/ # (It will grab this instead)
                - ...
        - src/ # (when it should be this.)
            library.js
    ```
    
    For right now, I'll leave it alone.
    """
    if directory.is_file():
        return None
    for entry in os.scandir(directory.path):
        if entry.is_file() or entry.name.startswith("."):
            continue
        if entry.name != "src":
            result = findSrc(entry)
            if result and result.name == "src":
                return result
        else:
            return entry
    return None

def parse_library(library_path: str, library_title: str, root_directory: str, license_path: str = None, contributors_path: str = None):

    try:
        cwd = os.getcwd()
        result = f"// #region {library_title}"
        if license_path is None:
            license_path = os.path.join(root_directory, "LICENSE")
        if contributors_path is None:
            contributors_path = os.path.join(root_directory, "CONTRIBUTORS")
        
        if os.path.isfile(license_path):
            result += f"\n/*\t{"="*8} LICENSE {"="*8}\n"
            with open(license_path,encoding="utf8") as f:
                while (line := f.readline()) != "":
                    result += f"\t{line}"
            result += f"\n\t{"="*8} LICENSE {"="*8}\t*/\n"
        
        result += f"\n/*\t{"="*8} CONTRIBUTORS {"="*8}\n"
        os.chdir(root_directory)
        contributors = subprocess.run("git shortlog -s",capture_output=True,text=True).stdout.replace(" ","").split("\t")
        for contributor in contributors[1:]:
            if (newline := contributor.rfind('\n')) > -1:
                contributor = contributor[:newline]
            result += f'\t{contributor} - code contributor\n'
        result = result[:len(result)-1]
        os.chdir(cwd)
        if os.path.isfile(contributors_path):
            with open(contributors_path, encoding="utf8") as f:
                while (line := f.readline()) != "":
                    result += f"\t{line}"
        result += f"\n\t{"="*8} CONTRIBUTORS {"="*8}\t*/\n"
        
        with open(library_path,encoding="utf8") as f:
            while (line := f.readline()) != "":
                result += f"{line}"
        result += "\n" * 2
        result += "// #endregion"
        result += "\n" * 2
    except Exception as e:
        raise OSError(f"[BUILD] Error: Unable to read {library_path}")
    return result
    
if __name__ == "__main__":
    PROJECT_NAME = ""
    PROJECT_NAME = len(PROJECT_NAME) > 0 and PROJECT_NAME or os.getcwd()[os.getcwd().rindex(os.sep) +1:] + " library.js"
    SRC_DIR = os.path.join("src")
    OUT_DIR = os.path.join("out")
    LIB_DIR = os.path.join("lib")
    LIBRARY_FILENAME = "library.js"
    LICENSE = os.path.join("LICENSE")
    
    OUT_JSCONFIG = {
        "compilerOptions": {
            "checkJs": False
        }
    }
    
    shutil.rmtree(OUT_DIR, True)
    os.mkdir(OUT_DIR)
    try: # To prevent vscode from complaining in the out directory.
        with open(os.path.join(OUT_DIR,"jsconfig.json"), "x", encoding="utf8") as f:
            f.write(json.dumps(OUT_JSCONFIG))
    except Exception as _:
        pass
    
    for entry in os.scandir(SRC_DIR):
        if entry.is_dir():
            continue
        if entry.name == LIBRARY_FILENAME:
            continue
        shutil.copy(entry.path, os.path.join(OUT_DIR,entry.name))

    bundled_library_content = parse_library(os.path.join(SRC_DIR,LIBRARY_FILENAME),PROJECT_NAME,os.curdir)

    for entry in os.scandir(LIB_DIR):
        lib_src = findSrc(entry)
        lib_file = os.path.join(lib_src, LIBRARY_FILENAME)
        lib_license = os.path.join(entry.path,LICENSE)

        if not os.path.isfile(lib_file):
            print(f"[BUILD] Warning: could not find \"{lib_file}\" for \"{entry.name}\"")
            continue
        bundled_library_content += parse_library(lib_file, entry.name, entry.path)
    with open(os.path.join(OUT_DIR,LIBRARY_FILENAME),"x",encoding="utf8") as f:
        f.write(bundled_library_content)
    print(f"[BUILD] Log: Built at {os.path.abspath(os.path.join(OUT_DIR))}")