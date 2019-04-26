import os
import sys
import getopt

"""
Use this module to automatically change .inp files based on a text file.
The text file should use the following formatting:
    All lines which being with a # will be ignored
    Lines which begin with -$Flag indicate the next lines contain text which 
        the function will search for
    Lines which begin with -$Insert indicate the next lines will be inserted 
        into the .inp file after any of the lines from the preceding -$Flag 
        statement are found
    To insert text at the beginning of a file, use the flag $StartOfFile
    To insert text at the end, use $EndOfFile

Call update_inp() to edit the .inp file.
"""


class SubFileGen:
    """
    makes a fancy generator out of a text file. creates an object that behaves
    like a generator but uses 'get_next()' instead of 'next().' the next
    subsequent call of the generator can be delayed using 'pause().'
    Automatically skips lines designated as comments by the characters
    defined in the 'comment_char_string' input. Tracks which line of the file
    the generator is on and stores it in self.line_number.
    """
    def __init__(self, sub_text_file_path, comment_char_string='#'):
        """

        :param sub_text_file_path: file path for containing the .txt file to
        be turned into a generator
        :param comment_char_string: string containing comment characters;
        lines beginning with any character in the string will be ignored
        """
        self.sub_text_file = open(sub_text_file_path)
        self.generator_obj = self.sub_text_file.__iter__()
        self.previous_line = None
        self.line_number = 0
        self.is_paused = False
        self.comment_chars = comment_char_string
        return

    def get_next(self):
        """
        gets the next line from the file (ignoring comment lines). if the
        file is 'paused' (self.is_paused), returns the previous line (
        self.previous_line)
        :return: a line from the file; either the next line or the previous
        line, depending on self.is_paused
        """
        if self.is_paused:
            line_to_return = self.previous_line
            self.un_pause()
        else:
            while True:
                line_to_return = self.generator_obj.next()
                self.line_number += 1
                self.previous_line = line_to_return
                for char in self.comment_chars:
                    if line_to_return.startswith(char):
                        break
                else:
                    break
        return line_to_return

    def get_line_number(self):
        """
        gets line number
        :return: integer corresponding to which line number the file last
        generated
        """
        return self.line_number

    def pause(self):
        """
        pauses the object
        :return: None
        """
        self.is_paused = True
        return

    def un_pause(self):
        """
        un-pauses the object
        :return: None
        """
        self.is_paused = False
        return

    def close_file(self):
        """
        closes substitute text file
        :return:
        """
        self.sub_text_file.close()
        return


class InpUpdateDict(dict):
    """
    subclassed from dictionary behaves as normal dictionary, but has two
    "queues" into which information waiting to be entered in the dict can be
    sorted.

    """
    def __init__(self, sub_text_file_path):
        """

        :param sub_text_file_path: file path for the substitute text file
        """
        super(InpUpdateDict, self).__init__()
        self.flag_queue = list()
        self.insert_queue = list()
        try:
            sub_gen = SubFileGen(sub_text_file_path)
            while True:
                try:
                    line = sub_gen.get_next()
                    if line.startswith('-$Flag'):
                        self.parse_flags(sub_gen)
                        continue
                    if line.startswith('-$Insert'):
                        self.parse_inserts(sub_gen)
                        continue
                except StopIteration:
                    if not len(self):
                        raise Exception("did not find any flag-insert pairs")
                    break
        finally:
            try:
                # noinspection PyUnboundLocalVariable
                sub_gen.close_file()
            except NameError:
                pass
        return

    def parse_flags(self, sub_gen_obj):
        """
        reads the separate lines after a '-$Flag' tag in the substitute text
        file and places them in self.flag_queue
        :param sub_gen_obj: SubFileGen object
        :return:
        """
        if self.flag_queue:
            raise Exception("misplaced '-$Flag' key in line "
                            "{0}".format(sub_gen_obj.get_line_number()))
        while True:
            try:
                line = sub_gen_obj.get_next()
            except StopIteration:
                raise Exception("found end of file while parsing '-$Flag' key")
            if line.startswith('-$'):
                break
            self.flag_queue.append(line.rstrip())

        if not self.flag_queue:
            raise Exception("empty '-$Flag' key in line "
                            "{0}".format(sub_gen_obj.get_line_number()))
        sub_gen_obj.pause()
        return

    def parse_inserts(self, sub_gen_obj):
        """
        reads the separate lines after a '-$Insert' tag in the substitute text
        file and places them in self.insert_queue
        :param sub_gen_obj: SubFileGen object
        :return:
        """
        if not self.flag_queue:
            raise Exception("misplaced '-$Insert' key in line "
                            "{0}".format(sub_gen_obj.get_line_number()))
        stop_exception = None
        while True:
            try:
                line = sub_gen_obj.get_next()
            except StopIteration as stop_exception:
                break
            if line.startswith('-$'):
                break
            self.insert_queue.append(line.rstrip())

        self.update_from_queues()
        if stop_exception:
            raise stop_exception
        else:
            sub_gen_obj.pause()
        return

    def update_from_queues(self):
        """
        creates dict entries with keys as the elements of self.flag_queue and
        values as the ENTIRE list in self.insert_queue
        :return:
        """
        if not self.flag_queue:
            raise Exception("flag_queue is empty")
        if not self.insert_queue:
            raise Exception("insert_queue is empty")
        for flag in self.flag_queue:
            if flag in self:
                raise Exception("{0} is a redundant flag".format(flag))
            self[flag] = self.insert_queue
        self.flag_queue = list()
        self.insert_queue = list()
        return

    def insert_lines(self, file_handle, test_line):
        """
        for a given key, if it exists in self (which is a dict), write the
        associated lines to the given file
        :param file_handle: file handle to which to write lines
        :param test_line: key to find values in self
        :return:
        """
        made_insertion = False
        for flag, lines_to_write in self.items():
            if test_line.startswith(flag):
                if made_insertion:
                    raise Exception("Line {0} matches multiple"
                                    " flags".format(test_line))
                for line in lines_to_write:
                    file_handle.write(line)
                    file_handle.write('\n')
                made_insertion = True
        return


def update_inp(inp_file_path, sub_text_file_path):
    """
    updates the inp file based on the substitution text file
    :param inp_file_path: path to the .inp file
    :param sub_text_file_path: path to the substitution text file
    :return:
    """
    inp_update_dict = InpUpdateDict(sub_text_file_path)
    with open(inp_file_path) as f:
        with open("temp.inp", 'w') as g:
            inp_update_dict.insert_lines(g, '$StartOfFile')
            while True:
                try:
                    line = f.next()
                except StopIteration:
                    break
                g.write(line)
                inp_update_dict.insert_lines(g, line)
            inp_update_dict.insert_lines(g, '$EndOfFile')
    os.remove(inp_file_path)
    os.rename("temp.inp", inp_file_path)
    return


def main(argv):
    inp_file_path = ''
    sub_text_file_path = ''
    try:
        opts, args = getopt.getopt(argv, "i:s:")
    except getopt.GetoptError:
        print('inp_editor.py -i <inp_file> -s <substitution_file>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-i':
            inp_file_path = arg
        elif opt == '-s':
            sub_text_file_path = arg
    update_inp(inp_file_path, sub_text_file_path)
    return


if __name__ == '__main__':
    default_input_file_name = 'example_inp.inp'
    default_substitute_file_name = 'example_subs_text.txt'
    if not sys.argv[1:]:
        cl_argv = ['-i', default_input_file_name,
                   '-s', default_substitute_file_name]
    else:
        cl_argv = sys.argv[1:]
    main(cl_argv)
    print("success")
