import os
import MySimpleGUI as sg
import subprocess
import sys
import subprocess
from pathlib import Path
import json
import collections

version = "1.0.0"


def blacken(blackbin, selection, linelength, target, skip_string_normalization):

    selection = [file for file in selection if Path(file).is_dir() or Path(file).is_file()]
    linelength_param = ["-l", str(linelength)]
    if target == "auto":
        target_param = []
    else:
        target_param = ["-t", target]
    if skip_string_normalization:
        skip_string_normalization_param = ["-S"]
    else:
        skip_string_normalization_param = []
    sp = subprocess.Popen([blackbin, *linelength_param, *target_param, *skip_string_normalization_param, *selection], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = sp.communicate()
    return "".join(c for c in err.decode("utf-8") if ord(c) < 255)


def load_config(file, window, selection):
    if Path(file).is_file():
        try:
            with open(file, "r") as f:
                settings = json.load(f)
                window.linelength.update(settings.get("linelength", 88))
                window.target.update(settings.get("target", "auto"))
                window.skip_string_normalization.update(settings.get("skip_string_normalization", False))
                window.files.update("")
                selection.clear()
                for item in settings.get("selection", []):
                    selection.append(item)
                    if Path(item).is_dir():
                        print(f"{sg.ansi.yellow}{item}{sg.ansi.reset}", file=window.files)
                    elif Path(item).is_file():
                        print(item, file=window.files)
                    else:
                        print(f"{sg.ansi.red}{item}{sg.ansi.reset}", file=window.files)
        except Exception as e:
            sg.popup(f"Error loading file {file}\n{e}", background_color="red", text_color="white", title="Error")

    else:
        sg.popup(f"{file} not found", background_color="red", text_color="white", title="Error")


def main():

    sg.theme("Black")
    sg.message_box_line_width(120)
    selection = []

    blackbin = "N/A"
    if sys.platform == "linux":
        black_bin = "/usr/local/bin/black"
    elif sys.platform == "darwin":
        black_bin = "/usr/local/black" 
    else:
        for path in sys.path:
            if (Path(path) / "black.exe").is_file():
                blackbin = str(Path(path) / "black.exe")
                break
            if (Path(path) / "Scripts" / "black.exe").is_file():
                blackbin = str(Path(path) / "Scripts" / "black.exe")
                break
    if blackbin == "N/A":
        sg.popup("black.exe not found. Make sure it is installed correctly.", background_color="red", text_color="white", title="Error")
        return

    json_file = "simply_black"
    optional = True
    if len(sys.argv) > 2:
        sg.popup(f"more then one parameter given", background_color="red", text_color="white", title="Error")
        json_file = "?"  # prevents a second error as optional = True
    else:
        if len(sys.argv) == 2:
            json_file = sys.argv[1]
            optional = False

    if Path(json_file).suffix == "":
        json_file += ".json"

    window = sg.Window(
        "simply_black",
        [
            [
                sg.FolderBrowse("Add folder", enable_events=True, key="add_folder", target=None, size=(12, 1)),
                sg.FilesBrowse("Add files", enable_events=True, key="add_files", file_types=((".py files", "*.py"),),target="add_files", size=(12, 1)),
                sg.Button("Clear selection", key="clear_selection", size=(12, 1)),
                sg.FileBrowse("Load config", key="load_config", size=(12, 1), target=None, initial_folder=".", file_types=((".json files", "*.json"),), enable_events=True),
                sg.SaveAs("Save config", key="save_config", target=None, initial_folder=".", file_types=((".json files", "*.json"),), size=(12, 1), enable_events=True),
                sg.Text("simply_black", font=("Courier", 20), size=(17, 1), justification="right"),
            ],
            [sg.Text("Selection")],
            [sg.Multiline(size=(120, 10), autoscroll=True, key="files")],
            [sg.Text("Line length (-l)", size=(25, 1)), sg.Slider(range=(80, 255), orientation="h", size=(71, 20), default_value=88, key="linelength")],
            [sg.Text("Target version (-t)", size=(25, 1)), sg.Combo(["auto", "py27", "py33", "py34", "py35", "py36", "py37", "py38"], size=(4, 1), default_value="auto", key="target")],
            [sg.Text("Skip string normalization (-S)", size=(25, 1)), sg.Checkbox("", key="skip_string_normalization", default=False)],
            [sg.Text("Output")],
            [sg.Multiline(size=(120, 10), autoscroll=True, auto_refresh=True, key="out")],
            [sg.Button("Blacken", size=(12, 1), key="blacken"), sg.Cancel("Exit", size=(12, 1), key="exit")],
        ],
    )
    window.finalize()

    if Path(json_file).is_file():
        load_config(file=json_file, window=window, selection=selection)
    else:
        if not optional:

            sg.popup(f"File {json_file} not found. Using default settings", background_color="red", text_color="white", title="Error")

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED or event == "exit":
            break
        if event == "add_folder":
            if values.add_folder:
                selection += [values.add_folder]
                print(f"{sg.ansi.yellow}{values.add_folder}{sg.ansi.reset}", file=window.files)
        if event == "add_files":
            if values.add_files:
                for file in values.add_files.split(";"):
                    print(file, file=window.files)
                    selection += [file]
        if event == "clear_selection":
            selection = []
            window.files.update("")

        if event == "blacken":
            window.out.update("Working ...\n")
            capture = blacken(blackbin=blackbin, selection=selection, linelength=int(values.linelength), target=values.target, skip_string_normalization=values.skip_string_normalization)
            window.out.update(capture)
            sg.popup("Done", background_color="grey", text_color="white", title="Ok")

        if event == "load_config":
            file = values.load_config
            if file:
                load_config(file=file, window=window, selection=selection)

        if event == "save_config":
            file = values.save_config
            if file:
                if Path(file).suffix == "":
                    file += ".json"
                settings = {"linelength": int(values.linelength), "target": values.target, "skip_string_normalization": values.skip_string_normalization, "selection": selection}
                try:
                    with open(file, "w") as f:
                        json.dump(settings, f)
                        sg.popup(f"Config saved as {file}", background_color="grey", text_color="white", title="Ok")
                except Exception as e:
                    sg.popup(f"Error saving file {file}\n{e}", background_color="red", text_color="white", title="Error")

    window.close()


if __name__ == "__main__":
    main()
