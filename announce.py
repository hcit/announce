# vim: sw=4 ts=4 noexpandtab
# For Python 2.6 with scapy

import sys
import string
import pprint
import json
from scapy.all import *

class Announcer:
	""" Announces people as they request their first DHCP lease of the day """

	people = []
	mac = dict()

	def __init__(self):
		self.load_people()
		print "Loaded people:"
		pprint.pprint(self.people)

	def load_people(self):
		try:
			with open('people.json', 'r') as f:
				self.people = json.load(f)
		except:
			print "Could not load people database"
			e = sys.exc_info()[1]
			pprint.pprint(e)

		for person in self.people:
			for mac_address in person["mac_addresses"]:
				self.mac[mac_address] = person

	def detect(self):
		sniff(filter="arp or (udp and (port 67 or 68))", prn=self.check_packet, store=0)

	def check_packet(self, packet):
		if DHCP in packet:
			source = packet[Ether].src
			print "Found DHCP request for MAC address: ", source

			if source in self.mac:
				person = self.mac[source]
				print "And it's one we're interested in, belonging to: ",
				print person["name"]

				if self.not_seen_today(person):
					print "And they're not seen today. Play the damn music!"
					self.announce(person)

	def not_seen_today(self, person):
		return True

	def announce(self, person):
		pass


announcer = Announcer();
announcer.detect();
