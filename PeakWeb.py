#!/usr/bin/python3
# (C) Kirils Solovjovs, 2020, https://kirils.org/
#
from datetime import datetime

import sys
if sys.version_info[0] <= 2: #dirty python2 hack to support utf8-sig
	from io import open
	
	
class OverwriteReader:
	
	def __init__(self,csv,separator=';',limit=-1):
		self.index = -1
		tmp = []
		self.data=[]
		for line in csv:
			tmp2=line.split(separator)
			for i in range(len(tmp2)):
				if tmp2[i]!="" or (limit>0 and i>limit):
					while i >= len(tmp):
						tmp.append("")
					tmp[i]=tmp2[i]
			
			self.data.append(tmp[:])

	def __iter__(self):
		return self
		
	def __next__(self):
		self.index += 1
		if self.index == len(self.data):
			raise StopIteration
		return self.data[self.index]
	
	def __getitem__(self,key):
		return self.data[key]
		
	def next(self): # python 2 compat
		return self.__next__()


class Peak:

	def validateDate(self,specialdates,dfrom,dto,wd,target):
		if type(target) is datetime:
			target = target.strftime('%Y-%m-%d')
		if target in specialdates: #unconditional match
			return True
		if dto is not None and target>dto:
			return False
		if dfrom is not None and target<dfrom:
			return False
		targetwd=datetime.strptime(target, '%Y-%m-%d').weekday() + 1
		if target in specialdates:
			targetwd=specialdates[target]
		
		return str(targetwd) in wd
		
	
	def fill(self,dest,value,count,maxcount):
		if not count:
			count = max(0, maxcount-len(dest) )
		for tmp in range(count):
			dest.append(value)
	
	def dateDeltaList(self,st):
		try:
			val=st.split(",")
			for n in range(len(val)):
				try:
					val[n] = int(val[n])
				except:
					val[n] = 0
				if n>0:
					val[n] += val[n-1]
					
			st=[self.date(x) for x in val]
		except:
			st=[]
			
		return st
		
	def clock(self,a):
		try:
			a=int(a)
			e=""
			while(a>=1440): # kas ar +1 dienu?
				a -= 1440
				e = " (+1)"
			return "%02d:%02d%s" % ( a/60 , a%60, e)
		except:
			return "ErrTime(%s)" % a
	
	def date(self,a):
		try:
			a=int(a)
			if a<=0:
				return None
			return datetime.utcfromtimestamp(a*86400).strftime('%Y-%m-%d')
		except:
			return "ErrDate(%s)" % a
	
	
	def __init__(self,*arg,**kwargs):
		header=kwargs['header'] if 'header' in kwargs else None
		self._valueindex=-1
		Peak._mapping = [ ]
		self.header=None
		if header is not None:
			self.header=header.lower().split(";")
		if (len(arg) == 0):
			raise TypeError("Class needs to be initialized with stop data.")
		if any ( isinstance(arg[x],list) for x in range(len(arg))):
			if len(arg) != 1:
				raise TypeError("If list is passed, it must be the only argument")	
			else:
				self.listinit(arg[0])
		else:
				self.listinit(arg)

	
	def __repr__(self):
		ra = []

		for n in range(len(self._mapping)):
			if getattr(self,self._mapping[n]) is None:
				continue
			r = "  '"
			r += self._mapping[n]
			r += "': "
			r += getattr(self,self._mapping[n]).__repr__()
			ra.append(r)
			
		return "<\n" + ",\n".join(ra) + "\n>\n"

	def __iter__(self):
		if hasattr(self,"value"):
			return self
		else:
			raise TypeError("Object needs 'value' to be iterated")
		
	def __next__(self):
		self._valueindex += 1
		if self._valueindex == len(self.value):
			raise StopIteration
		return list(self.value)[self._valueindex]
	
	def __getitem__(self,key):
		if hasattr(self,"value"):
			return self.value[key]
		else:
			raise TypeError("Object needs 'value' to be indexed")
		
	def next(self): # python 2 compat
		return self.__next__()
			
	def listinit(self,stopdata):
		raise NotImplementedError


class PeakSpecialDates(Peak):
	
	_mapping = [
		"value",
	]
	
	def listinit(self,rt):
		
		for i in range(len(rt),13):
			rt.append(None)
		
		rt[0]={x:rt[11] for x in self.dateDeltaList(rt[5]) if x is not None}

		for n in range(len(PeakSpecialDates._mapping)):
			setattr(self,PeakSpecialDates._mapping[n],rt[n])
			
			
class PeakStop(Peak):
	
	_mapping = [
		"id",
		"direction",
		"coord_lat", #lat
		"coord_long", #lng
		"neighbours", #stops
		"name",
		"info",
		"street",
		"area",
		"city",
	]
	

	def listinit(self,stopdata):
		if not self.header:
			self.header = self._mapping

		for i in range(len(stopdata),len(self.header)+5):
			stopdata.append(None)

		for n in range(len(PeakStop._mapping)):
			setattr(self,PeakStop._mapping[n],None)
			
		for n in range(len(self.header)):
			setattr(self,self.header[n],stopdata[n])
	
		if hasattr(self,"stops"): self.neighbours = self.stops
		if hasattr(self,"lat"): self.coord_lat = self.lat
		if hasattr(self,"lng"): self.coord_long = self.lng
			
		try: self.neighbours=self.neighbours.split(",")
		except:	pass
			
		try: self.coord_lat=int(self.coord_lat)/100000
		except: pass
				
		try: self.coord_long=int(self.coord_long)/100000
		except: pass
			
			
class PeakRoute(Peak):

	def timeConv(self,timestring):
		parsed={
			'departures':[],
			'validity_from':[],
			'validity_to':[],
			'weekdays':[],
			'tags':[],
		}
		numbers=timestring.split(",")
		
		timebase=0
		vehcount=0
		
		stage=0
		pairing=0
		mem=None
		relive_ptr=0
		prevmem=0
		
		for i in numbers:
			empty = i==''
			i_string = i
			
			try:
				i = int(i)
			except:
				i = 0
			
			if stage>0:
				pairing = (pairing+1) % 2
				if pairing:
					mem=i
					continue
					
			if stage==0 and not empty:
				timebase += i
				parsed['departures'].append(timebase)
				vehcount=len(parsed['departures'])
				
				if len(i_string) > 2 and (i_string[0:3] == '-00' or i_string[0:2] == '+0'):
					tag = '4'
				elif (len(i_string) > 1 and i_string[0:2] == '-0' or len(i_string)>0 and i_string[0] == '+'):
					tag = '1'
				else:
					tag = '0'
				parsed['tags'].append(tag)
				
			elif stage==1:
				self.fill(parsed['validity_from'],self.date(mem),i,vehcount)
			elif stage==2:
				self.fill(parsed['validity_to'],self.date(mem),i,vehcount)
			elif stage==3:
				self.fill(parsed['weekdays'],str(mem),i,vehcount)
			elif stage>3: #can't have "else" here!
				if empty:
					i=vehcount - relive_ptr%vehcount
					
				for tmp in range(i):
					parsed['departures'].append(parsed['departures'][relive_ptr]+mem+prevmem)
					relive_ptr += 1
					
				prevmem += mem-5

			if empty:
				stage += 1
				prevmem = 0

		parsed['departures']=[self.clock(x) for x in parsed['departures']]

		return parsed


	_mapping = [
		"number", #routenum
		"authority",
		"city",
		"transport",
		"operator",
		"validity", #validityperiods
		"specialdates",
		"tag",
		"direction", #routetype
		"commercial",
		"name",
		"weekdays",
		"streets",
		"stops",
		#"timetables",
		#"timetables_by_stops",
		#"timetables_by_vehicles",
		"realstreets",
		"weekday_list",
		"special",
		"id",		
	]
	
	def listinit(self,rt):
		if not self.header:
			self.header = self._mapping
		
		for i in range(len(rt),len(self.header)+5):
			rt.append(None)
	
		for n in range(len(PeakRoute._mapping)):
			setattr(self,PeakRoute._mapping[n],None)
			
		for n in range(len(self.header)):
			setattr(self,self.header[n],rt[n])
	
		try: self.routestops=self.routestops.split(",")
		except:	pass

		if hasattr(self,"routenum"): self.number = self.routenum
		if hasattr(self,"routetype"): self.direction = self.routetype
		if hasattr(self,"routestops"): self.stops = self.routestops
		if hasattr(self,"routetag"): self.tag = self.routetag
		if hasattr(self,"routename"): self.name = self.routename
		if hasattr(self,"validityperiods"): self.validity = self.validityperiods
					
		self.validity=[x for x in self.dateDeltaList(self.validity)]
		
		self.specialdates=[x for x in self.dateDeltaList(self.specialdates) if x is not None] #probably wrong
		
		self.timetables=rt[14]	
		
		# expressbuss, if starts with 3
		if self.transport.lower() == 'minibus' and len(self.number)==3 and self.number[0]>='3' and self.city.lower() == 'riga':
			self.transport = 'expressbus'
		
		self.id = self.transport+"/"+self.number+"/"+self.direction


		self.timetables=self.timeConv(self.timetables)

		# night bus parse to move to proper weekdays for Riga
		if self.transport.lower() == 'nightbus' and self.weekdays =='67' and self.city.lower() == 'riga':
			self.weekdays = '56'
			self.timetables["weekdays"] = ['56' if x == '67' else x for x in self.timetables["weekdays"] ]
		
		if ('s' in self.weekdays):
			self.special = "medium"
			
		self.weekday_list=sorted(set(self.timetables["weekdays"]))
		vehcount=len(self.timetables["weekdays"])


		self.timetables_by_stops=[]
		self.timetables_by_vehicles=[{'schedule':[]} for i in range(vehcount)]
		
		
		d = 0
		for nextstop in self.stops:
			n = 0
			stopval=[]
			for time in self.timetables["departures"][0+d:vehcount+d]:
				if d==0:
					self.timetables_by_vehicles[n]['weekdays'] =self.timetables["weekdays"][n]
					self.timetables_by_vehicles[n]['date_from'] = self.timetables["validity_from"][n]
					self.timetables_by_vehicles[n]['date_to'] =self.timetables["validity_to"][n]
					self.timetables_by_vehicles[n]['specialdates'] =self.specialdates
					self.timetables_by_vehicles[n]['route'] =self.id
				stopval.append({
					'stop': nextstop,
					'departure': time,
					'weekdays': self.timetables["weekdays"][n],
					'date_from': self.timetables["validity_from"][n],
					'date_to': self.timetables["validity_to"][n],
					'tag': self.timetables["tags"][n],
					'specialdates': self.specialdates,
					'route': self.id,
				})
				self.timetables_by_vehicles[n]["schedule"].append({
					'stop': nextstop,
					'departure': time,
					'tag': self.timetables["tags"][n],
				})
				
				n += 1
			self.timetables_by_stops.append(stopval)
			d += vehcount


class PeakWebReader(Peak):

	def __init__(self,routesin,stopsin):
		self.stops={}
		self.routes={}
		self.subroutes={}
		self.specialdates={}
		self.addStops(stopsin)
		self.addRoutes(routesin)
		

	def addStops(self,stopsin):
		for stop in OverwriteReader(stopsin[1:]):
			st=PeakStop(stop,header=stopsin[0])
			self.stops[st.id]=st
		
	def addRoutes(self,routesin):					
		routesjoined=[]

		for i in routesin:
			if(i.find(';SpecialDates;',0,14)==0):
				if self.specialdates != {}:
					print ("Warning! Overwriting global special dates with new data.") 
				self.specialdates=PeakSpecialDates(OverwriteReader([i])[0])
				break
		
		for i in range(3 if routesin[2][0] == ';' else 2 if routesin[1][0] == ';' else 1,len(routesin),2):
			try:
				routesjoined.append(routesin[i]+routesin[i+1])
			except:
				print ("Warning! Wrong line count in routes.") 

		for route in OverwriteReader(routesjoined,limit=11):
			rt=PeakRoute(route,header=routesin[0])
			self.subroutes[rt.id]=rt
			try:
				self.routes[rt.transport+"/"+rt.number]
			except:
				self.routes[rt.transport+"/"+rt.number]=[]
			self.routes[rt.transport+"/"+rt.number].append(rt.id)

	
	def FindRoutesAtStop(self,stopid):
		ra=[]
		for r in self.subroutes:
			if stopid in self.subroutes[r].stops:
				ra.append(self.subroutes[r].id)
		return ra
	
	
	def GetRoutes(self,base="",every=False):
		if(base.count('/')==2): # 3 parts
			if base in self.subroutes: 
				return [base]
			else:
				return []
		
		if(base.count('/')==1): #2 parts
			every=True
			
		if (every):
			if base == "": #0 parts
				return self.subroutes
			return [i for i in self.subroutes if self.subroutes[i].id.find(base+"/") == 0]  #1 and 2 parts
		else:
			if(base == ""): #0 parts
				return list(set([self.subroutes[i].transport for i in self.subroutes ]))
			else:
				return list(set([base+"/"+self.subroutes[i].number for i in self.subroutes if self.subroutes[i].transport==base])) #1 parts
			
			
	def GetDeparturesForRouteAtStop(self,routeid,stopid):
		ra=[]
		for r in self.subroutes[routeid].timetables_by_stops:
			for r1 in r:
				if r1['stop'] == stopid:
					ra.append(r1)
		return ra
		
	def GetDeparturesAtStop(self,stopid):
		ra=[]
		for r in self.FindRoutesAtStop(stopid):
			ra = ra + (self.GetDeparturesForRouteAtStop(r,stopid))
		return ra
		
	def FilterByDate(self,fullresult,date=None):
		ra=[]
		if date is None:
			date=datetime.now().strftime('%Y-%m-%d')
		for r in fullresult:
			if(self.validateDate(r['specialdates'],r['date_from'],r['date_to'],r['weekdays'],date)):
				ra.append(r)
		return ra

	def SortByDeparture(self,fullresult):
		return sorted(fullresult, key = lambda i: 
			("99" if (i['departure'].find('(+1)')!=-1) else "0")+" "+i['departure'])
			
	def PopulateRouteStreets(self):

		for ro in self.subroutes:
			realstreets=[]
			thisroute=self.subroutes[ro]
			striter = thisroute.streets.split(",")
			stopcopy=thisroute.stops[:]
			striter = striter + ['']*(len(stopcopy)-len([x for x in striter if x=='']))
			for i in range(len(striter)):
				if striter[i] == '':
					try:
						striter[i]=self.stops[stopcopy[0]].street
						stopcopy.pop(0)
					except:
						striter[i]=""
					
			for st in striter:
				if st == '0' or st=='' or st is None:
					continue
				if len(realstreets)==0 or realstreets[-1]!=st:
					realstreets.append(st)
			self.subroutes[ro].realstreets=",".join(realstreets)
		
	
	def PopulateAll(self):
		self.PopulateRouteStreets()
		


class PeakWebFileReader(PeakWebReader):

	def __init__(self,froutes,fstops):
		PeakWebReader.__init__(self,self.open(froutes),self.open(fstops))
	
	def open(self,filename):
		return open(filename,encoding='utf-8-sig').read().strip().split('\n')
	
	def addFile(self,routes=None,stops=None):
		if stops is None and routes is None:
			raise TypeError("File for stops or routes need to be specified.")
		if stops is not None:
			self.addStops(self.open(stops))
		if routes is not None:
			self.addRoutes(self.open(routes))
			
