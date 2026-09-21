# If no LTE connection is available
/ip dhcp-client add interface=bridge disabled=no

# DNS settings
/ip dns set servers=8.8.8.8,1.1.1.1

# update packages
/system package update check-for-updates

# Release the serial port from the RouterOS console first.
# Run these inspection commands over Ethernet, WinBox, or SSH.
/port print detail
/system console print detail

# The output shows console entry 0 using serial0. Disable it using a network
# session; this can disconnect a terminal connected through serial0.
/system console disable 0

# Confirm serial0 is no longer marked as used by the console, then configure
# the GPS receiver (adjust the port for your device).
/port print detail
/system gps set enabled=yes port=serial0

# Monitor GPS status after the port has been assigned.
/system gps monitor

# Send the current coordinates to the REST API every minute.
# Replace the URL with the reachable address of the Python server.
/system script add name=send-gps-location source={
	:local latitude [/system gps get latitude]
	:local longitude [/system gps get longitude]

	# RouterOS reports 0/0 when there is no valid GPS fix.
	:if (($latitude = 0) and ($longitude = 0)) do={
		:log warning "GPS has no fix; location was not sent"
		:return
	}

	# The API assigns a UTC timestamp when recorded_at is omitted.
	:local payload ("{\"latitude\":" . $latitude . ",\"longitude\":" . $longitude . "}")

	:do {
		/tool fetch url="http://3.121.113.5:8000/locations" \\
			http-method=post \\
			http-header-field="Content-Type: application/json" \\
			http-data=$payload \\
			output=none
		:log info ("GPS location sent: " . $latitude . "," . $longitude)
	} on-error={
		:log error "Could not send GPS location to REST API"
	}
}

/system scheduler add name=send-gps-location interval=1m on-event=send-gps-location start-time=startup

# Run once manually to test it:
# /system script run send-gps-location


