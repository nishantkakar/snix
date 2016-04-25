#!/usr/bin/env python
import logging
import snixCore

class ColorizedStreamHandler(logging.StreamHandler):
		
	color_map = {
		'red':1,
		'green':2,
		'yellow':3,
		'white':7,
	}

	level_map = {
		logging.DEBUG: ('white', True),
		logging.INFO: ('green', False),
		logging.WARNING: ('yellow', False),
		logging.ERROR: ('red', False),
		logging.CRITICAL: ('red', True),
	}

	csi = '\x1b['
	reset = '\x1b[0m'

	def emit(self, record):
		message = logging.StreamHandler.format(self,record)
		stream = self.stream
		if not getattr(stream, 'isatty', None):
			stream.write(message)
		else:
			stream.write(self.colorize(message,record))
		stream.write(getattr(self, 'terminator', '\n'))
		self.flush()
			
	def colorize(self, message,record):
		if record.levelno in self.level_map:
			fg, bold = self.level_map[record.levelno]
			params=[]
			if fg in self.color_map:
				params.append(str(self.color_map[fg]+30))
			if bold:
				params.append('1')
			if params:
				message = ''.join((self.csi, ';'.join(params),'m',message,self.reset)) 
		return message

class SnixLogger:
	"""A Colorized Logger that can be used aross Snix. This is a singleton. """
	__metaclass__ = snixCore.Singleton

	def __init__(self):
		self.logger = logging.getLogger("SNIX")
		self.logger.setLevel(logging.DEBUG)
		formatter=logging.Formatter("%(asctime)s-%(levelname)s-%(message)s", "%m/%d/%Y %I:%M:%S %p")
		handler = ColorizedStreamHandler()
		handler.setFormatter(formatter)
		self.logger.addHandler(handler)

	@staticmethod
	def logger():
		return SnixLogger().logger

#TODO : Convert this into a unit test.
if __name__ == "__main__":
	logger = SnixLogger.logger() 
	logger.info("hello")
	logger.debug("blah")
	logger.error("oops")
	logger.critical("gah")
