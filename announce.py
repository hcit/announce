# vim: sw=4 ts=4 noexpandtab
#
# For Python 2.6+
#
# Dependencies:
#  - scapy
#  - dateutil
#  - pygame

import sys
import string
import json
import dateutil.parser
import pyaudio
import mad
import numpy
from datetime import datetime
from scapy.all import *

class Announcer:
	""" Announces people as they request their first DHCP lease of the day """

	people = []
	mac = dict()
	name = dict()
	audio = None

	def __init__(self):
		self.load_people()

		print 'Loaded people:'
		for p in self.people:
			print p['name'],

		self.setup_audio()
		self.announce(self.name['Dominic'])

	def load_people(self):
		try:
			with open('people.json', 'r') as f:
				self.people = json.load(f)
		except:
			print 'Could not load people database.'

		for person in self.people:
			# Optional parameters
			if not 'seek' in person:
				person['seek'] = 0

			if not 'duration' in person:
				person['duration'] = 20

			self.name[person['name']] = person
			for mac_address in person['mac_addresses']:
				self.mac[mac_address] = person


	def setup_audio(self):
		self.audio = pyaudio.PyAudio()

	def detect(self):
		sniff(filter='arp or (udp and (port 67 or 68))', prn=self.check_packet, store=0)

	def check_packet(self, packet):
		if DHCP in packet:
			source = packet[Ether].src
			print 'Found DHCP request for MAC address: ', source

			if source in self.mac:
				person = self.mac[source]
				print 'And it is one we are interested in, belonging to: ',
				print person['name']

				if self.not_seen_today(person):
					print 'And they have not been seen today. Play the damn music!'
					self.announce(person)
				else:
					print 'But they have already been seen.'

				self.save_seen(person)


	def not_seen_today(self, person):
		not_seen_in = datetime.now() - dateutil.parser.parse(person['last_seen'])
		return not_seen_in.days > 0 or not_seen_in.seconds > (10 * 60 * 60)


	def save_seen(self, person):
		person['last_seen'] = datetime.now().isoformat(' ')

		try:
			with open('people.json', 'w') as f:
				f.write(json.dumps(self.people, sort_keys=True, indent=4))
		except:
			print 'Could not persist last seen datetime.'


	def announce(self, person):
		# Open MP3
		try:
			music = mad.MadFile(person['audio'])
			print "Audio file loaded: %s" % person['audio']
		except:
			print "Could not open audio file: %s" % person['audio']
			raise

		# Open output
		try:
			stream = self.audio.open(output = True,
					channels = 2,
					format =
					self.audio.get_format_from_width(pyaudio.paInt32),
					rate = music.samplerate())
		except:
			print "Could not open output stream"
			raise

		# Play
		try:
			seek_msec = person['seek'] * 1000
			fadeout_msec = (person['seek'] + person['duration']) * 1000
			total_msec = (person['seek'] + person['duration'] + person['fade']) * 1000

			data = music.read()

			# Seek
			while data != None and music.current_time() <= seek_msec:
				data = music.read() # Throw away

			# Full volume
			while data != None and music.current_time() <= fadeout_msec:
				stream.write(data)
				data = music.read()

			# Fadeout
			volume = 1.0 * (2 ** 32)
			while data != None and music.current_time() <= total_msec:
				print "Starting fadeout"

				#	b = [(d * volume) for d in data]A
				b = numpy.frombuffer(data, dtype = numpy.int16) * volume
				stream.write(b)

				data = music.read()


		except:
			print "Error while outputting audio"
			raise

		stream.close()
		music.close()

		print "Done announcing"

announcer = Announcer();
announcer.detect();
