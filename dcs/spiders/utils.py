"""
Defines utility functions and more.
"""

def file_path_substitution(path: str) -> str:
    """Replace illegal characters in file paths with legal ones
    Illegal characters replaced: \\ / : * ? " < > | """
    str_path = str(path) # in case path is Path for example
    str_path = str_path.replace("\\", "＼")
    str_path = str_path.replace("/", "／")
    str_path = str_path.replace(":", "：")
    str_path = str_path.replace("*", "＊")
    str_path = str_path.replace('"', "''")
    str_path = str_path.replace("<", "＜")
    str_path = str_path.replace(">", "＞")
    str_path = str_path.replace("|", "｜")
    return str_path