filename="owasp_static_android.txt"
try:
    with open(filename, "r") as file:
        lines_in_file = file.read().splitlines()
except IOError:
    print("could not open file '%s'." % filename)
line_index = 1
try:
    for line in lines_in_file:
        line_index = line_index + 1

        print(str(line.split('|||')[0]) + "|||" + str(line.split('|||')[1]) + "|||" + str(
                line.split('|||')[3]) + ": " + str(line.split('|||')[2]))
except IOError:
    print("Format is not readable or file is missing: %s." % filename)