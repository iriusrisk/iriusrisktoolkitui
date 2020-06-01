windows_line_ending = b'\r\n'
linux_line_ending = b'\n'

def convertCRLFtoLF(path):
	with open(str(path), 'rb') as f:
		content = f.read()
		content = content.replace(windows_line_ending, linux_line_ending)
		f.close()

	with open(str(path), 'wb') as f:
		f.write(content)
		f.close()
