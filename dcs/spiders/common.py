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
    str_path = str_path.replace("?", "？")
    str_path = str_path.replace("\n", "")
    str_path = str_path.replace("\r", "")
    return str_path

def strip_list(str_list: list[str], chars: str = "\r\n\t 　") -> list[str]:
    """Returns a copy of given list with all items stripped of given characters."""
    return [a.strip(chars) for a in str_list]