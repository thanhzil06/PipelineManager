import os
import re


class FileCleaner:
    """This class will clean any file before any treatment"""

    def __init__(self, filepath):
        self.filepath = filepath  # define a current path
        self.filepathout = ""  # path of the outfile
        self.fencoding = "iso-8859-1"
        self.fencodingout = "utf8"

    @staticmethod
    def remove_double_quote(line):
        hasdblquote = re.match(r"(.+)\"\"(.+)", line)
        if hasdblquote is not None:
            line = re.sub(r"\"\"", "", line, flags=re.MULTILINE)
        return line  # suppress to allow processing

    @staticmethod
    def remove_p_br(line):
        regex = r"\<p\>|\<\/p\>|\<br\/\>"
        subst = ""
        hasdp_br = re.match(regex, line)
        if hasdp_br is not None:
            line = re.sub(regex, subst, line, 0)
        return line  # suppress to allow processing

    def cleaning_odxfile(self, pathout):
        odxfile = open(self.filepath, "r", encoding=self.fencodingout)
        try:
            odxfileout = open(pathout, "x", encoding=self.fencodingout)
        except FileExistsError:
            print("The file allready exists, it will be removed the recreated")

        odxlines = odxfile.readlines()
        for line in odxlines:
            nline = line.replace("<p>", "")
            nline = nline.replace("</p>", "")
            nline = nline.replace("<br/>", "")
            odxfileout.write(nline)

    def cleaning_file(self, pathout):
        a2lfile = open(self.filepath, "r", encoding=self.fencoding)
        try:
            a2lfileout = open(pathout, "x", encoding=self.fencodingout)
        except FileExistsError:
            print("The file allready exists, it will be removed the recreated")
            os.remove(pathout)
            a2lfileout = open(pathout, "x", encoding=self.fencodingout)

        a2lines = a2lfile.readlines()
        for line in a2lines:
            nline = self.remove_double_quote(line)
            a2lfileout.write(nline)
