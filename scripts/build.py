import os
import shutil
import json

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

def composeRegionHeaders(headerTitle: str, javascriptContents: str):
    return (
f"""// #region {headerTitle}


{javascriptContents}

// #endregion

"""
    )

if __name__ == "__main__":
    PROJECT_NAME = ""
    PROJECT_NAME = len(PROJECT_NAME) > 0 and PROJECT_NAME or os.getcwd()[os.getcwd().rindex(os.sep) +1:] + " library.js"
    SRC_DIR = os.path.join("src")
    OUT_DIR = os.path.join("out")
    LIB_DIR = os.path.join("lib")
    LIBRARY_FILENAME = "library.js"
    
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

    try:
        with open(os.path.join(SRC_DIR,LIBRARY_FILENAME)) as f:
            bundled_library_content = composeRegionHeaders(PROJECT_NAME, f.read())
    except Exception as e:
        raise OSError(f"[BUILD] Error: Unable to read ${os.path.join(SRC_DIR,LIBRARY_FILENAME)}")

    for entry in os.scandir(LIB_DIR):
        lib_src = findSrc(entry)
        lib_file = os.path.join(lib_src, LIBRARY_FILENAME,)
        if not os.path.isfile(lib_file):
            print(f"[BUILD] Warning: could not find \"{lib_file}\" for \"{entry.name}\"")
            continue
        try:
            with open(lib_file, encoding="utf8") as f:
                bundled_library_content += composeRegionHeaders(entry.name, f.read())
        except Exception as e:
            print(f"[BUILD] Warning: could not read library file for \"{entry.name}\"\n\n{e}")
    with open(os.path.join(OUT_DIR,LIBRARY_FILENAME),"x",encoding="utf8") as f:
        f.write(bundled_library_content)
    print(f"[BUILD] Log: Built at {os.path.abspath(os.path.join(OUT_DIR))}")