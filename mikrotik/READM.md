
--- LTE route -----------------------------------------------------------------

remove eth1 route
```
/ip dhcp-client remove [find interface=ether1]
```

If no LTE connection is available
```
/ip dhcp-client add interface=bridge add-default-route=no disabled=no
```

first routeis is to LTE
```
/ip route print
#Flags: X - disabled, A - active, D - dynamic, C - connect, S - static, r - rip, b - bgp, o - ospf, m - mme, B - blackhole, U - unreachable, P - prohibit
      DST-ADDRESS        PREF-SRC        GATEWAY            DISTANCE
 0 ADS  0.0.0.0/0                          lte1                      2
 1 ADC  192.168.1.0/25     192.168.1.80    bridge                    0
 2 ADC  192.168.88.0/24    192.168.88.1    bridge                    0
 3 ADC  213.175.79.181/32  213.175.79.181  lte1                      0
```

get public ip
```
/ip address print
#Flags: X - disabled, I - invalid, D - dynamic
      ADDRESS           NETWORK         INTERFACE
 0   ;;; defconf
     192.168.88.1/24    192.168.88.0    bridge
 1 D 213.175.79.181/32  213.175.79.181  lte1
 2 D 192.168.1.80/25 192.168.1.0        bridge
```

test NAT
```
/interface list> /ip firewall nat print
Flags: X - disabled, I - invalid, D - dynamic
 0    ;;; defconf: masquerade
      chain=srcnat action=masquerade out-interface-list=WAN ipsec-policy=out,none
```

--- LTE route -----------------------------------------------------------------

APN profile (apn + pin )
```
/interface lte apn set [find default=yes] apn="internet.lmt.lv"
/interface lte set lte1 pin="****"
```
verify
```
/interface lte info lte1 once
           pin-status: ok
  registration-status: registered
        functionality: full
         manufacturer: "MikroTik"
                model: "R11e-LTE"
             revision: "MikroTik_CP_2.160.000_v015"
     current-operator: LV LMT
                  lac: 40191
       current-cellid: 3753490
               enb-id: 14662
            sector-id: 18
           phy-cellid: 276
    access-technology: Evolved 3G (LTE)
       session-uptime: 1h9m30s
                 imei: 355654096516674
                 imsi: 247010604372140
                 uicc: 8937101122502211407f
               earfcn: 6300 (band 20, bandwidth 10Mhz)
                 rsrp: -91dBm
                 rsrq: -12dB
                 sinr: 5dB
                  cqi: 6
```

--- System --------------------------------------------------------------------

DNS settings
```
/ip dns set servers=8.8.8.8,1.1.1.1
```

update packages
```
/system package update check-for-updates
```

enable winbox access
```
/ip firewall filter add chain=input action=accept protocol=tcp dst-port=8291 in-interface=lte1 place-before=0 comment="Allow WinBox over LTE"
```
--- GPS -----------------------------------------------------------------------

Release the serial port from the RouterOS console first.
```
/port print detail
/system console print detail
```

The output shows console entry 0 using serial0. Disable it using a network
session; this can disconnect a terminal connected through serial0.
```
/system console disable 0
```

Confirm serial0 is no longer marked as used by the console, then configure
the GPS receiver (adjust the port for your device).
```
/port print detail
```
```
/system gps set enabled=yes port=serial0 gps-antenna-select=external
/port set 0 baud-rate=auto data-bits=8 flow-control=none name=serial0 parity=none stop-bits=1
```
Monitor GPS status after the port has been assigned.
```
/system gps monitor
```

--- GPS Script ----------------------------------------------------------------

Send the current coordinates to the REST API every minute.
Replace the URL with the reachable address of the Python server.
```
/system script remove [find name=send-gps-location]
/system script add name=send-gps-location policy=read,write,test source={
    # The position comes from monitor; "get" only returns GPS settings.
    :local gps [/system gps monitor once as-value]

    # The receiver reports NMEA degrees and minutes (5656.6891 = 56 deg 56.6891 min).
    # Convert to decimal degrees with integer maths, since RouterOS has no floats.
    # Assumes the northern and eastern hemispheres (no sign is reported).
    :local toDecimal do={
        :local s [:tostr $1]
        :local dot [:find $s "."]
        :local ip [:pick $s 0 $dot]
        :if ([:len $ip] < 4) do={ :return $s }
        :local fp [:pick ([:pick $s ($dot + 1) [:len $s]] . "0000") 0 4]
        # Strip leading zeros so :tonum does not read the value as octal.
        :while (([:len $ip] > 1) and ([:pick $ip 0 1] = "0")) do={ :set ip [:pick $ip 1 [:len $ip]] }
        :while (([:len $fp] > 1) and ([:pick $fp 0 1] = "0")) do={ :set fp [:pick $fp 1 [:len $fp]] }
        :local n [:tonum $ip]
        :local micro [:tostr (((($n % 100) * 10000) + [:tonum $fp]) * 100 / 60)]
        :while ([:len $micro] < 6) do={ :set micro ("0" . $micro) }
        :return (($n / 100) . "." . $micro)
    }

    :if ((($gps->"valid") != true) and (($gps->"valid") != "yes")) do={
        :log warning "GPS has no fix; location was not sent"
    } else={
        # The API assigns a UTC timestamp when recorded_at is omitted.
        :local payload ("{\"latitude\":" . [$toDecimal ($gps->"latitude")] . ",\"longitude\":" . [$toDecimal ($gps->"longitude")] . "}")

        :do {
            /tool fetch url="http://3.121.113.5:8000/locations" http-method=post http-header-field="Content-Type: application/json" http-data=$payload output=none
            :log info ("GPS location sent: " . $payload)
        } on-error={
            :log error ("Could not send GPS location to REST API: " . $payload)
        }
    }
}
```

```
/system scheduler remove [find name=send-gps-location]
/system scheduler add name=send-gps-location interval=1m on-event=send-gps-location start-time=startup policy=read,write,test
```
Test it by hand and read the log:
```
/system gps monitor once
/system script run send-gps-location
/log print where message~"GPS"
```

--- Dynamic DNS ---------------------------------------------------------------
```
/ip cloud set ddns-enabled=yes
/ip cloud print
```