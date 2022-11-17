"""Main script to check for potential vc crashes."""
import sys
import os

hex_characters = ("0","1","2","3","4","5","6","7","8","9","a","b","c","d","e","f","A","B","C","D","E","F")

def pruneLine(line):
    return line.replace("\t","").replace("\n","").strip()

def scan_file(file: str):
    """Scan file for any operations which may crash Wii U VC."""
    with open(file, "r") as c_file:
        lines = c_file.readlines()
        static_definitions = [pruneLine(x).split(" ")[1] for x in lines if x.strip()[:len("#define")] == "#define"]
        # Variable Modulo checker
        lines_with_potential_modulo = [pruneLine(x) for x in lines if "%" in x]
        if len(lines_with_potential_modulo) > 0:
            modulo_ends = []
            for x in lines_with_potential_modulo:
                modulo_started = -1
                indentation = 0
                for char_idx, char in enumerate(x):
                    if char == "%":
                        modulo_started = char_idx
                    elif char == "(" and modulo_started != -1:
                        indentation += 1
                    elif char == ")" and modulo_started != -1:
                        indentation -= 1
                        if indentation < 0:
                            modulo_ends.append(x[modulo_started+1:char_idx])
                            modulo_started = -1
                    elif char in ("]","}","=") and modulo_started != -1 and indentation == 0:
                        modulo_ends.append(x[modulo_started+1:char_idx])
                        modulo_started = -1
                    elif char == ";" and modulo_started != -1:
                        modulo_ends.append(x[modulo_started+1:char_idx])
                        modulo_started = -1
            for m in modulo_ends:
                error = ""
                is_error = False
                if len([x for x in m.strip() if x == "\""]) % 2:
                    # Odd number of quotations, assume part of printf format string
                    is_error = False
                elif m.strip().isnumeric():
                    # Is base 10 number, skip
                    is_error = False
                elif "0x" in m.strip() and len([x for x in m.strip().split("0x")[1] if x not in hex_characters]) == 0:
                    # Is base 16 number, skip
                    is_error = False
                elif m.strip() in static_definitions:
                    # Is static definition
                    is_error = False
                elif len([x for x in m.strip() if x not in ("0","1","2","3","4","5","6","7","8","9","+","-","*","/",",")]) > 0:
                    is_error = True
                    print(f"{file}: Error with line segment {m}, detected potential modulo with volatile variable b where the format of a%b.")
                else:
                    print(m)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pth = sys.argv[1]
        if os.path.exists(pth):
            file_list = []
            if os.path.isfile(pth):
                # Is File
                file_list = [pth]
            else:
                # Is Directory
                for path, subdirs, files in os.walk(pth):
                    file_list.extend([os.path.join(path,x) for x in files if os.path.join(path, x)[-2:] == ".c"])
            if len(file_list) > 0:
                for file in file_list:
                    scan_file(file)
            else:
                print("ERROR: No *.c files found in this directory")
                sys.exit()
        else:
            print("ERROR: Path doesn't exist")
            sys.exit()
    else:
        print("ERROR: No files specified")
        sys.exit()