#!/usr/bin/python3

from PeakWeb import PeakWebFileReader

RSRMS = PeakWebFileReader("routes.txt","stops.txt")
RSRMS.addFile(routes="routes-rms.txt",stops="stops-rms.txt")

departues_at_stop_8002=RSRMS.SortByDeparture(RSRMS.FilterByDate(RSRMS.GetDeparturesAtStop('8002')))

#print (RSRMS.stops)
#print (RSRMS.subroutes)
print (RSRMS.subroutes["expressbus/346/a-b"])
print (RSRMS.subroutes["nightbus/N1/a-b"] )

for stop in RSRMS.subroutes["nightbus/N1/a-b"].timetables_by_stops:
	print ([onestop["departure"]+"/"+onestop["tag"] 
		for onestop in stop
			if onestop["weekdays"] == RSRMS.subroutes["nightbus/N1/a-b"].weekday_list[0]], 
	RSRMS.stops[stop[0]["stop"]].name)


