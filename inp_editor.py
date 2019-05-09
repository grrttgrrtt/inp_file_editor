import os
import sys
import getopt

"""
Use this module to automatically change .inp files based on a text file.
The text file should use the following formatting:
    All lines which being with a # will be ignored (use for comments)
    
    Lines which begin with -$Flag indicate the next lines contain 'flag' text
        'Flag' text should match the following format:
            <n1>, <line 1>
            <n2>, <line 2>
        etc. (without <>'s), where line 1, line 2, etc. contain the text to be
        matched and n1, n2, etc. specifies how many lines to skip before
        performing the $Isert or $Replace action. Setting n = 0 will insert
        immediately after the line, or replace that line. Lines which are
        skipped are NOT checked for matching flags.
        
    Lines which begin with -$Insert indicate the next lines will be inserted 
        into the .inp file after any of the lines from the preceding -$Flag 
        statement are found
        
    Lines which begin with -$Replace indicate the next lines will replace lines
        after any of the lines from the preceeding -$Flag statement are found
        
    To insert/replace text at the beginning of a file, use the flag $StartOfFile
    To insert text at the end, use $EndOfFile

To use as a standalone, change the following variables in the block at the 
end of the file:
    default_input_file_name: inp file you wish to modify
    default_substitute_file_name: text file, formatted as above, detailing 
        the insertions to be made
        
To use from the command line, call node_snap.py with the following options 
corresponding to the variables listed above:
    -i: input_file_name
    -s: substitute_file_name
    
To use from another module, import and call the function update_inp() with 
the above options as arguments.

Changelog:
05-02-2019 -Created
05-09-2019 -Added "replace" functionality; modified SubFileGen to just read all
            lines on initialization instead of holding an open file in memory
           -Updated flag functionality to allow skipping a set number of lines
            after a flag before performing edit
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
    def __init__(self, sub_text_file_object, comment_char_string='#'):
        """

        :param sub_text_file_path: file path for containing the .txt file to
        be turned into a generator
        :param comment_char_string: string containing comment characters;
        lines beginning with any character in the string will be ignored
        """
        self.generator_obj = sub_text_file_object.__iter__()
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
                line_to_return = next(self.generator_obj)
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
    def __init__(self, sub_text_file_object):
        """

        :param sub_text_file_object: open file object for the substitute text
            file
        """
        super(InpUpdateDict, self).__init__()
        self.lines_after = 0
        self.flag_queue = list()
        self.action_queue = list()
        sub_gen = SubFileGen(sub_text_file_object)
        while True:
            try:
                line = sub_gen.get_next()
                if line.startswith('-$Flag'):
                    self.parse_flags(sub_gen)
                    continue
                if line.startswith('-$Insert'):
                    self.parse_actions(sub_gen,'i')
                    continue
                if line.startswith('-$Replace'):
                    self.parse_actions(sub_gen,'r')
                    continue
            except StopIteration:
                if not len(self):
                    raise Exception("did not find any flag-insert pairs")
                break
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
            line_parts = line.split(', ',1)
            if len(line_parts) != 2:
                raise Exception("bad line format for line "
                                "{0}".format(sub_gen_obj.get_line_number()))
            self.lines_after = int(line_parts[0])
            if self.lines_after < 0:
                raise Exception("bad value for lines_after in line "
                                "{0}".format(sub_gen_obj.get_line_number()))
            self.flag_queue.append(line_parts[1].rstrip())

        if not self.flag_queue:
            raise Exception("empty '-$Flag' key in line "
                            "{0}".format(sub_gen_obj.get_line_number()))
        sub_gen_obj.pause()
        return

    def parse_actions(self, sub_gen_obj, mode):
        """
        reads the separate lines after a '-$Insert' or '-$Replace' tag in the
        substitute text file and places them in self.action_queue
        :param sub_gen_obj: SubFileGen object
        :param mode: character indicating if lines are for insertion or
            replacement
        :return:
        """
        if mode not in ['i', 'r']:
            raise Exception("bad mode")
        if mode == 'i':
            key = '-$Insert'
        if mode == 'r':
            key = '-$Replace'
        if not self.flag_queue or self.action_queue:
            raise Exception("misplaced '{0}' key in line "
                            "{1}".format(key, sub_gen_obj.get_line_number()))
        stop_exception = None
        while True:
            try:
                line = sub_gen_obj.get_next()
            except StopIteration as e:
                stop_exception = e
                break
            if line.startswith('-$'):
                break
            self.action_queue.append(line.rstrip())

        self.update_from_queues(mode)
        if stop_exception:
            raise stop_exception
        else:
            sub_gen_obj.pause()
        return
                            

    def update_from_queues(self, mode):
        """
        creates dict entries with keys as the elements of self.flag_queue and
        values as the ENTIRE list in self.action_queue
        :param mode: character indicating if lines in action_queue are for
            insertion or replacement
        :return:
        """
        if not self.flag_queue:
            raise Exception("flag_queue is empty")
        if not self.action_queue:
            raise Exception("action_queue is empty")
        for flag in self.flag_queue:
            if flag in self:
                raise Exception("{0} is a redundant flag".format(flag))
            self[flag] = (self.lines_after, mode, self.action_queue)
        self.lines_after = 0
        self.flag_queue = list()
        self.action_queue = list()
        return

    def act_on_lines(self, inp_file_object, temp_inp_file_object, test_line):
        """
        for a given key, if it exists in self (which is a dict), write the
        associated lines to the given file
        :param temp_inp_file_object: open file object to which to write lines
        :param test_line: key to find values in self
        :return:
        """
        made_change = False
        for flag, action_tuple in self.items():
            if test_line.startswith(flag):
                if made_change:
                    raise Exception("Line {0} matches multiple"
                                    " flags".format(test_line))
                lines_to_skip, mode, lines_to_write = action_tuple
                if test_line in ['$StartOfFile', '$EndOfFile']:
                    line_to_write = ''
                else:
                    line_to_write = test_line
                if mode == 'i':
                    lines_to_skip += 1
                while True:
                    temp_inp_file_object.write(line_to_write)
                    lines_to_skip -= 1
                    if lines_to_skip:
                        line_to_write = next(inp_file_object)
                    else:
                        break
                for line_to_write in lines_to_write:
                    temp_inp_file_object.write(line_to_write)
                    temp_inp_file_object.write('\n')
                    if mode == 'r':
                        next(inp_file_object)
                made_change = True
        if not made_change:
            if test_line not in ['$StartOfFile', '$EndOfFile']:
                temp_inp_file_object.write(test_line)
        return


def update_inp(inp_file_path, sub_text_file_path):
    """
    updates the inp file based on the substitution text file
    :param inp_file_path: path to the .inp file
    :param sub_text_file_path: path to the substitution text file
    :return:
    """
    with open(sub_text_file_path) as f:
        inp_update_dict = InpUpdateDict(f)
        with open(inp_file_path) as g:
            with open("temp.inp", 'w') as h:
                inp_update_dict.act_on_lines(g, h, '$StartOfFile')
                while True:
                    try:
                        line = next(g)
                    except StopIteration:
                        break
                    inp_update_dict.act_on_lines(g, h, line)
                inp_update_dict.act_on_lines(g, h, '$EndOfFile')
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
    default_input_file_name = 'example_inp - Copy.inp'
    default_substitute_file_name = 'example_subs_text.txt'
    if not sys.argv[1:]:
        cl_argv = ['-i', default_input_file_name,
                   '-s', default_substitute_file_name]
    else:
        cl_argv = sys.argv[1:]
    main(cl_argv)
    print("success")
