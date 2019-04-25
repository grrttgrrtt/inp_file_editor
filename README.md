# inp_file_editor
You can use this to quickly make changes to an .inp file, or a group of .inp files.

It requires an .inp file and a .txt file which contains instructions for what to substitute.

You may use the script as a standalone, or import it as a module into your own python script (useful for using it on a batch of .inp files). 

To use as a standalone, it may be convenient to place the script, the .inp file, and the .txt file all in the same directory.
To run the script using the command prompt, open the command prompt and navigate to the directory in question. Then, enter “inp_editor.py -i <inp_file_name.inp> -s <substitution_script_name.txt>” without quotes or <>’s, where inp_file_name.inp is the name of your .inp file and substitution_script_name.txt is the name of your substitution script. 

You may also run the script by editing it, saving it, and then running it (either through the command line or by double-clicking on it). To do so, open the script in a text editor and scroll to the end. Underneath the line that reads “if __name__ == ‘__main__’:”, edit the values for default_input_file_name and default_substitute_file_name.  Then, save the script and run it.

To use the script as a module in another python script, use the import command at the start of your script (import inp_editor). Make sure a copy of inp_editor.py is saved in the same location as the python script you are writing. You can then call the function inp_editor.update_inp(inp_file_path, sub_text_file_path), again where inp_file_path is the path to your .inp file and sub_text_file_path is the path to your substitute text file.

The substitute text file consists of pairs of “flag” (-$Flag) tags and “insert” (-$Insert) tags. Tags should be entered on the line with nothing else. Lines which begin with a # will be ignored. Every flag tag is expected to be followed, at some point, by an insert tag. Each line after a flag tag is saved as a flag until the corresponding insert tag is reached. Each line after an insert tag is saved as a block of text which corresponds to the preceding flags. This text will be inserted into the .inp file depending on where the flags are found. 

The script reads an .inp file and tests each line to see if it begins with any of the flags from the substitute text file. If it does the block of text from the corresponding insert flag is inserted into the .inp file after the matching line. Be specific with flags; if two duplicate flags are entered, the script raises an error. If a line begins with multiple tags, the script will raise an error.

Keep in mind that, for a flag-insert pair, all of the lines after the insert statement will be inserted after any of its flags are found. I haven’t found a use for having multiple flags in a flag-insert pair, but you might. 
To insert text at the beginning of an .inp file, use the $StartOfFile flag. To insert text at the end of an .inp file, use the $EndOfFile flag.

Files for an example are included. Placing all files in the same directory and running the script will run on the example files by default. The included .inp file is heavily abridged to maintain a small file size; it will not run in Abaqus, but it serves to illustrate the script functionality.
