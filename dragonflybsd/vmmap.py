python
def slave_pid():
		s = gdb.execute("maint print target-stack", to_string=True)
		if "remote" in s:
			import os
			p = os.popen('ps a|fgrep valgrind')
			s = p.read().split('\n')[0].split()[0]
			p.close()
			return int(s)
		elif "native" in s:
			return gdb.selected_inferior().pid
		else:
			raise Exception("No slave pid found")

class SlavePID(gdb.Command):
	def __init__(self):
		super().__init__("slave-pid", gdb.COMMAND_USER)
	def invoke(self, arg, from_tty):
		print(slave_pid())

def open_mem(pid):
	return open(f'/proc/{pid}/mem', 'rb')

def open_map(pid):
	return open(f'/proc/{pid}/map')

def find_offset(pid, addr, filename, rchunk, schunk):
	with open_mem(pid) as fp:
		fp.seek(addr)
		searchbuf = fp.read(rchunk)
	with open(filename, 'rb') as fp:
		offset = 0
		while 1:
			buf = fp.read(rchunk)
			if not buf or searchbuf == buf:
				break
			offset += rchunk
	return offset

"""
usage: vmmap [address]
"""
class VMMAP(gdb.Command):
	def __init__(self):
		super().__init__("vmmap", gdb.COMMAND_USER)
		self.nsearch = 1024
		self.pagesize = 4096
	def invoke(self, arg, from_tty):
		from colored import fg, bg, attr
		addr = int(gdb.parse_and_eval(arg)) if len(arg) >= 1 else None
		rel = None
		pid = slave_pid()
		with open_map(pid) as fp:
			for ln in fp.read().split('\n')[:-1]:
				items = ln.split()
				start = int(items[0], 16)
				end = int(items[1], 16)
				if addr and (addr >= start) and (addr < end):
					rel = addr - start
					if items[-1] == '-':
						offset = 0
					else:
						offset = find_offset(pid, start, items[-1], self.nsearch, self.pagesize)
					print(f'{bg("red")}{ln}{attr(0)}{fg("red")} @ {hex(offset)}{attr(0)}')
				else:
					print(ln)
		if rel:
			print(f'{fg("red")}rel {hex(rel)}{attr(0)}')

SlavePID()
VMMAP()
end

