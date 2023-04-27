def prRed(prt):
    print("\033[91m{}\033[00m".format(prt))
def prGreen(prt):
    print("\033[92m{}\033[00m".format(prt))
def prPurple(prt):
    print("\033[95m{}\033[00m".format(prt))
def prYellow(prt):
    print("\033[93m{}\033[00m".format(prt))
def print_ansi_colour(text, ansi_colour, **kwargs):
    """Prints text in the specified ANSI colour."""
    """https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797"""
    print(u"\u001b[38;5;" + f"{str(ansi_colour)}m{text}\033[00m", **kwargs)