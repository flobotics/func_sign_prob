import subprocess
import os

pickle_file_name_dir = '/tmp/src-code//ubuntu_src_pkgs/usepackage/usepackage-1.13'

pickle_file_name = 'usepackage'

os.chdir(pickle_file_name_dir)

print(f'start')

# out = subprocess.run(["gdb", 
#                           "-ex",
#                           "file {}".format(pickle_file_name),
#                           "-ex",
#                           "info functions"],
#                           capture_output=True, 
#                           universal_newlines=True)
# gdb_out = out.stdout
# print(f'gdb_out:{gdb_out}')


proc = subprocess.Popen(["gdb", 
                        "-ex",
                        "file {}".format(pickle_file_name),
                        "-ex",
                        "info functions"], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE, 
                         encoding='utf-8',
                         errors='replace', 
                         universal_newlines=True )

while proc.poll() is None:
    line = proc.stdout.readline()
    print(f'>{line}<')


print(f'end')
# output = proc.communicate()[0]
# print(output)

# print(f'out >{proc.stdout.read()}<')








