# If no LTE connection is available
/ip dhcp-client add interface=bridge disabled=no

# DNS settings
/ip dns set servers=8.8.8.8,1.1.1.1

# update packages
/system package update check-for-updates

# monitor GPS status
/system gps monitor