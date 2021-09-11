
Download firmware from https://ofmodemsandmen.com/firmware.html

Flash to the Pi's micro SD using the PI's imager.



## Access Web Portal
Default networking will be configured to 192.168.1.1.

Navigate to https://192.168.1.1. No password to start with.

## Set password
Go to System -> Administration -> set password

## Configure SSH access if desired
Naviate to System -> Administration -> SSH Access
1. Set interface to lan
2. Turn off password authentication
3. Turn off allow root logins with password
4. Turn off Gateway ports
5. Save.

Navigate to System -> Administration -> SSH Keys
1. Add the public key as needed

## Update the network
Naviate to Network -> Interfaces -> LAN -> Edit
1. Change IPv4 address to 192.168.11.1 (for example)
2. Change DNS to Cloudflare's 1.1.1.1 & 1.0.0.1
3. Save, and again on the interfaces page. Might need to re-acquire the DHCP lease on the client side.

## Disable WIFI (we don't want this)
Navigate to Network -> Wireless
1. Disable the "ROOter 5G" SSID. This should also disable the Wifi radio.


## Configure Time Zone
Navigate to System -> System -> General Settings
1. Set time zone to America/Chicago
2. Save & Apply


## Configure modem connection profiles
Navigate to Modem -> Connection Profile

Configure Default Profile
1. Set APN to `fast.t-mobile.com`
2. Save & Apply

## Configure TTL (if needed)
Navigate to Network -> Firewall -> Custom TTL
1. Click Enabled
2. Set TTL Value to 64 (or whatever is needed, maybe 65)
3. Save & Apply
