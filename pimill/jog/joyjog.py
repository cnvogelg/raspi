import time
import pygame
import ConfigParser

class JoyJogMgr:
	"""Detects and creates JoyJog instances for matching joystick devices

		reads joystick definition from 'joy.cfg' file.
		only joysticks described there are mapped!
	"""

	def __init__(self, jogger):
		pygame.joystick.init()
		self.jogger = jogger
		self._load_cfg()
		self._joys = []

	def _load_cfg(self):
		self._cfg = ConfigParser.SafeConfigParser()
		self._cfg.read('joy.cfg')

	def scan(self):
		num = pygame.joystick.get_count()
		for i in xrange(num):
			joy = pygame.joystick.Joystick(i)
			name = joy.get_name()
			# is joy in config?
			if self._cfg.has_section(name):
				(axes, buttons) = self._parse_axes_and_buttons(name)
				if len(axes) > 0 or len(buttons) > 0:
					kwargs = self._parse_kwargs(name)
					joy.init()
					jj = JoyJog(self.jogger, joy, axes, buttons, *kwargs)
					self._joys.append(jj)

	def _parse_kwargs(self, sect_name):
		kwargs = {}
		# TODO
		return kwargs

	def _parse_axes_and_buttons(self, sect_name):
		axes = {}
		buttons = {}
		for name, value in self._cfg.items(sect_name):
			# axis<num> = ...
			if name.startswith("axis"):
				num = int(name[4:])
				axes[num] = value
			# button<num> = ...
			elif name.startswith("button"):
				num = int(name[6:])
				buttons[num] = value
		return axes, buttons

	def get_num_joys(self):
		return len(self._joys)

	def get_joys(self):
		return self._joys

	def handle_event(self, ev):
		for joy in self._joys:
			joy.handle_event(ev)

	def handle_tick(self):
		for joy in self._joys:
			joy.handle_tick()


# axis flags
AFLAG_FAST = 0x01
AFLAG_SLOW = 0x02
AFLAG_INVERT = 0x4
AFLAG_REPEAT = 0x8

# button types
BUTTON_MOVE = 0x01
BUTTON_HOME = 0x02
BUTTON_LABEL = 0x03
BUTTON_GOTO = 0x04

# button flags
BFLAG_NEGATE = 0x01
BFLAG_FAST = 0x02
BFLAG_SLOW = 0x04
BFLAG_REPEAT = 0x08


class JoyRepeat:
	def __init__(self, start=0.3, interval=0.2,
				 progress_step=4, progress_interval=0.05,
				 progress_min=0.05):
		self.start = start
		self.interval = interval
		self.progress_step = progress_step
		self.progress_interval = progress_interval
		self.progress_min = progress_min

	def create_state(self, now):
		return [self.interval, 0, now, True]

	def update_state(self, now, state):
		delta = now - state[2]
		first = state[3]
		if first:
			interval = self.start
		else:
			interval = state[0]
		if delta >= interval:
			# update state
			state[2] = now
			state[3] = False
			# progress?
			if self.progress_step > 0 and not first:
				state[1] += 1
				if state[1] == self.progress_step:
					state[1] = 0
					# update interval
					if state[0] > self.progress_min:
						state[0] -= self.progress_interval
			return True
		else:
			return False


class JoyJog:
	"""Use a USB HID Joystick as a jog device
	"""

	def __init__(self, jogger, joy, axes, buttons,
				 axis_repeat=None,
				 button_repeat=None,
		         axis_dead_zone=0.01):
		"""Use a given pygame joystick with the given mappings as a jog device.

		   Typically JoyJogMgr will create these instances automatically.
		   But you can also create one manually if you like.

		   'joy' - already initialized pygame.joystick.Joystick instance

			'axes' is a dictionary mapping joystick axis numbers to jog axis.
			Allowed axis are 'X', 'Y', 'Z'
				'R' modifier to allow repeat
				'I' invert axis
				'F' 'faster' motion
				'S' 'slower' motion

			axes = {
				0 : 'XR',
				5 : 'YRF'
			}

			'buttons' is dictionary mapping joystick buttons to jog actions.
			Actions are:

			'M+X', 'M-X', 'M+Y', 'M-Y', 'M+Z', 'M-Z'   move in direction
				'R'   modifier for direction: allow repeat
				'F'   'faster' motion
				'S'   'slower' motion

			'HX', 'HY', 'HZ', 'HXY', HXYZ' - home one, more, or all axis
			'L' - label position
			'G' - goto label

			''

			butons = {
				0 : '+X',
				1 : 'XH'
				2 : '+YF'
			}

			'axis_repeat' - describes auto repeat of axis
			'button_repeat' - describes auto repeat of buttons 
			'axis_dead_zone' - absolute value considered axis zero
		"""
		self.jogger = jogger
		self.joy = joy
		self.joy_id = joy.get_id()
		self.axes = axes
		self.buttons = buttons
		
		if axis_repeat is None:
			self.axis_repeat = JoyRepeat()
		else:
			self.axis_repeat = axis_repeat 

		self.axis_dead_zone = axis_dead_zone

		if button_repeat is None:
			self.button_repeat = JoyRepeat()
		else:
			self.button_repeat = button_repeat

		# setup axes and buttons
		self._parse_axes()
		self._parse_buttons()
		# build repeat map
		self.armap = [None] * len(self.amap)
		self.brmap = [None] * len(self.bmap)

	def __str__(self):
		return "[%s:axis=%s,buttons=%s]" % (self.joy.get_name(), self.amap, self.bmap)

	def _parse_axes(self):
		self.amap = []
		for i in xrange(self.joy.get_numaxes()):
			if i in self.axes:
				self.amap.append(self._parse_axis(self.axes[i]))
			else:
				self.amap.append(None)

	def _parse_axis(self, val):
		val = val.lower()
		
		# get axis index
		index = 0
		if 'x' in val:
			index = 0
		elif 'y' in val:
			index = 1
		elif 'z' in val:
			index = 2

		# flags
		flags = 0
		if 'i' in val:
			flags |= AFLAG_INVERT
		if 'f' in val:
			flags |= AFLAG_FAST
		if 's' in val:
			flags |= AFLAG_SLOW

		return (index, flags)

	def _parse_buttons(self):
		self.bmap = []
		for i in xrange(self.joy.get_numbuttons()):
			if i in self.buttons:
				self.bmap.append(self._parse_button(self.buttons[i]))
			else:
				self.bmap.append(None) 

	def _parse_button(self, val):
		val = val.lower()

		btype = None

		# button type
		if 'm' in val:
			btype = BUTTON_MOVE
		elif 'h' in val:
			btype = BUTTON_HOME
		elif 'l' in val:
			btype = BUTTON_LABEL
		elif 'g' in val:
			btype = BUTTON_GOTO

		# button index
		bindex = None
		if 'x' in val:
			bindex = 0
		if 'y' in val:
			bindex = 1
		if 'z' in val:
			bindex = 2

		# button flags
		bflags = 0
		if '-' in val:
			bflags |= BFLAG_NEGATE
		if 'f' in val:
			bflags |= BFLAG_FAST
		if 's' in val:
			bflags |= BFLAG_SLOW
		if 'r' in val:
			bflags |= BFLAG_REPEAT

		return (btype, bindex, bflags)

	def handle_event(self, ev):
		"""call to handle suitable pygame events"""
		now = time.time()
		if ev.type == pygame.JOYAXISMOTION:
			if ev.joy == self.joy_id:
				return self._handle_axis(ev.axis, ev.value, now)
		elif ev.type == pygame.JOYBUTTONDOWN:
			if ev.joy == self.joy_id:
				return self._handle_button(True, ev.button, now)
		elif ev.type == pygame.JOYBUTTONUP:
			if ev.joy == self.joy_id:
				return self._handle_button(False, ev.button, now)
		return False

	def _handle_axis(self, axis, value, now):
		a = self.amap[axis]
		# axis is mapped -> get mapping (index, flags)
		if a is not None:
			# axis zero?
			if abs(value) <= self.axis_dead_zone:
				# clear repeat
				self.armap[axis] = None
				value = 0.0
			else:
				# limit axis
				if value > 1.0:
					value = 1.0
				elif value < -1.0:
					value = -1.0
				# set repeat:
				state = self.axis_repeat.create_state(now)
				self.armap[axis] = [value, state]
			# perform move on jogger
			self._do_axis(a, value)
			return True
		else:
			return False

	def _do_axis(self, axis_data, value):
		# tell jogger to move
		axis_index = axis_data[0]
		axis_flags = axis_data[1]
		if self.jogger is not None:
			self.jogger.move_axis(axis_index, value)
		else:
			print "do_axis", axis_index, axis_flags, value

	def _handle_button(self, down, num, now):
		b = self.bmap[num]
		# button is mapped -> get mapping (btype, bflags)
		if b is not None:
			# button pressed -> keep start time
			if down:
				# set repeat:
				self.brmap[num] = self.button_repeat.create_state(now)
				# perform button action
				self._do_button(b)
			else:
				# clear repeat timer 
				self.brmap[num] = None
			return True
		else:
			return False

	def _do_button(self, button_data):
		btype = button_data[0]
		bindex = button_data[1]
		bflags = button_data[2]
		if btype == BUTTON_MOVE:
			self._do_button_move(bindex, bflags)

	def _do_button_move(self, bindex, bflags):
		if bflags & BFLAG_NEGATE:
			value = -1.0
		else:
			value = 1.0
		if self.jogger is not None:
			self.jogger.move_axis(bindex, value)
		else:
			print "do_move", bindex, bflags, value

	def handle_tick(self):
		"""call in regular intervals (tick timer) to handle timing stuff

			does auto repeat handling for buttons and axis
		"""
		now = time.time()
		self._handle_button_repeat(now)
		self._handle_axis_repeat(now)

	def _handle_axis_repeat(self, now):
		# check axis
		for i in xrange(len(self.armap)):
			repeat = self.armap[i]
			if repeat is not None:
				value = repeat[0]
				r = repeat[1]
				if self.axis_repeat.update_state(now, r):
					self._do_axis(self.amap[i], value)

	def _handle_button_repeat(self, now):
		# check buttons
		for i in xrange(len(self.brmap)):
			repeat = self.brmap[i]
			if repeat is not None:
				if self.button_repeat.update_state(now, repeat):
					self._do_button(self.bmap[i])


if __name__ == '__main__':
	jjm = JoyJogMgr(None)
	jjm.scan()
	for joy in jjm.get_joys():
		print joy

