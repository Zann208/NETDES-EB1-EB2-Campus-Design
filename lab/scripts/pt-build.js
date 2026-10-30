// Packet Tracer 9.0 build script for the EB1-EB2 lab.
// This is the script that cabled, addressed and renamed lab/NETDES-EB1-EB2.pkt.
//
// How to run: Extensions > Scripting > Edit File Script Module.
//   General tab: tick Application, IPC, Get Network Info, Change Network Info.
//   Script Engine tab: add a file, paste this script, open Debug, press Run File.
//
// Expects devices placed with Packet Tracer's default names (left column of NAMES).
// Port choices match lab/cabling.md. Cable types: 8100 straight-through, 8101 cross-over.

var n = ipc.network();
var lw = ipc.appWindow().getActiveWorkspace().getLogicalWorkspace();
var log = [];
var ST = 8100, CR = 8101;

function link(a, pa, b, pb, t) {
  try {
    var la = n.getDevice(a).getPort(pa).getLink(), lb = n.getDevice(b).getPort(pb).getLink();
    if (la || lb) { log.push('SKIP ' + a + ' ' + pa + ' - ' + b + ' ' + pb); return; }
    log.push((lw.createLink(a, pa, b, pb, t) ? 'OK   ' : 'FAIL ') + a + ' ' + pa + ' - ' + b + ' ' + pb);
  } catch (e) { log.push('ERR  ' + a + ' ' + pa + ' - ' + b + ' ' + pb + ' : ' + e); }
}

function host(name, ip, mask, gw) {
  try {
    var p = n.getDevice(name).getPort('FastEthernet0');
    if (ip) { p.setDhcpClientFlag(false); p.setIpSubnetMask(ip, mask); p.setDefaultGateway(gw); }
    else { p.setDhcpClientFlag(true); }
    p.setDnsServerIp('8.8.8.8');
    log.push('HOST ' + name + ' ' + (ip || 'DHCP'));
  } catch (e) { log.push('ERR host ' + name + ' : ' + e); }
}

// --- Transit and edge ------------------------------------------------------
link('Router1', 'GigabitEthernet0/0', 'Switch0', 'FastEthernet0/1', ST);              // ITSC-R - ITSC-SW
link('Switch0', 'FastEthernet0/2', 'Router0', 'GigabitEthernet0/0/0', ST);            // ITSC-SW - FW01 outside
link('Switch0', 'FastEthernet0/3', 'Router2', 'GigabitEthernet0/0/0', ST);            // ITSC-SW - FW02 outside
link('Router0', 'GigabitEthernet0/0/2', 'Router2', 'GigabitEthernet0/0/2', CR);       // HA heartbeat
link('Router0', 'GigabitEthernet0/0/1', 'Multilayer Switch1', 'GigabitEthernet1/0/22', ST);
link('Router2', 'GigabitEthernet0/0/1', 'Multilayer Switch1', 'GigabitEthernet1/0/21', ST);
link('Multilayer Switch1', 'GigabitEthernet1/0/7', 'Wireless LAN Controller0', 'GigabitEthernet1', ST);

// --- EB2 -----------------------------------------------------------------
link('Multilayer Switch1', 'GigabitEthernet1/0/3', 'Switch4', 'GigabitEthernet0/1', CR);
link('Multilayer Switch1', 'GigabitEthernet1/0/4', 'Switch4', 'GigabitEthernet0/2', CR);
link('Multilayer Switch1', 'GigabitEthernet1/0/5', 'Multilayer Switch4', 'GigabitEthernet1/0/1', CR);
link('Multilayer Switch1', 'GigabitEthernet1/0/6', 'Multilayer Switch4', 'GigabitEthernet1/0/2', CR);
link('Multilayer Switch4', 'GigabitEthernet1/0/3', 'Switch5', 'GigabitEthernet0/1', CR);
link('Multilayer Switch4', 'GigabitEthernet1/0/4', 'Switch5', 'GigabitEthernet0/2', CR);
link('Multilayer Switch4', 'GigabitEthernet1/0/5', 'Switch6', 'GigabitEthernet0/1', CR);
link('Multilayer Switch4', 'GigabitEthernet1/0/6', 'Switch6', 'GigabitEthernet0/2', CR);

// --- Inter-building and EB1 -----------------------------------------------
link('Multilayer Switch1', 'GigabitEthernet1/0/1', 'Multilayer Switch0', 'GigabitEthernet1/0/1', CR);
link('Multilayer Switch1', 'GigabitEthernet1/0/2', 'Multilayer Switch0', 'GigabitEthernet1/0/2', CR);
link('Multilayer Switch0', 'GigabitEthernet1/0/3', 'Switch1', 'GigabitEthernet0/1', CR);
link('Multilayer Switch0', 'GigabitEthernet1/0/4', 'Switch1', 'GigabitEthernet0/2', CR);
link('Multilayer Switch0', 'GigabitEthernet1/0/5', 'Multilayer Switch2', 'GigabitEthernet1/0/1', CR);
link('Multilayer Switch0', 'GigabitEthernet1/0/6', 'Multilayer Switch2', 'GigabitEthernet1/0/2', CR);
link('Multilayer Switch0', 'GigabitEthernet1/0/7', 'Multilayer Switch3', 'GigabitEthernet1/0/1', CR);
link('Multilayer Switch0', 'GigabitEthernet1/0/8', 'Multilayer Switch3', 'GigabitEthernet1/0/2', CR);
link('Multilayer Switch2', 'GigabitEthernet1/0/3', 'Switch2', 'GigabitEthernet0/1', CR);
link('Multilayer Switch2', 'GigabitEthernet1/0/4', 'Switch2', 'GigabitEthernet0/2', CR);
link('Multilayer Switch3', 'GigabitEthernet1/0/3', 'Switch3', 'GigabitEthernet0/1', CR);
link('Multilayer Switch3', 'GigabitEthernet1/0/4', 'Switch3', 'GigabitEthernet0/2', CR);

// --- Hosts -----------------------------------------------------------------
link('PC0', 'FastEthernet0', 'Switch4', 'FastEthernet0/2', ST);   // EB2 staff
link('PC1', 'FastEthernet0', 'Switch4', 'FastEthernet0/6', ST);   // EB2 student test port
link('PC2', 'FastEthernet0', 'Switch4', 'FastEthernet0/7', ST);   // EB2 guest test port
link('PC5', 'FastEthernet0', 'Switch4', 'FastEthernet0/5', ST);   // camera stand-in
link('PC6', 'FastEthernet0', 'Switch4', 'FastEthernet0/4', ST);   // printer stand-in
link('PC3', 'FastEthernet0', 'Switch3', 'FastEthernet0/2', ST);   // EB1 staff
link('PC7', 'FastEthernet0', 'Switch3', 'FastEthernet0/5', ST);   // camera stand-in
link('PC8', 'FastEthernet0', 'Switch3', 'FastEthernet0/4', ST);   // printer stand-in
link('PC4', 'FastEthernet0', 'Multilayer Switch1', 'GigabitEthernet1/0/23', ST);  // admin PC
link('Server0', 'FastEthernet0', 'Multilayer Switch1', 'GigabitEthernet1/0/24', ST); // NVR
// The 2960-24TT has no PoE, so the AP takes PoE from a 3650-24PS port.
link('Light Weight Access Point0', 'GigabitEthernet0', 'Multilayer Switch1', 'GigabitEthernet1/0/20', ST);

host('PC0'); host('PC1'); host('PC2'); host('PC3');
host('PC4', '10.10.16.30', '255.255.255.192', '10.10.16.1');
host('Server0', '10.10.16.70', '255.255.255.224', '10.10.16.65');
host('PC5', '10.10.15.10', '255.255.255.224', '10.10.15.1');
host('PC6', '10.10.14.138', '255.255.255.128', '10.10.14.129');
host('PC7', '10.10.6.10', '255.255.255.224', '10.10.6.1');
host('PC8', '10.10.5.138', '255.255.255.128', '10.10.5.129');

// --- Rename to design Device IDs ------------------------------------------
var NAMES = [
  ['Router1', 'ITSC-R'], ['Switch0', 'ITSC-SW'],
  ['Router0', 'EB2-MDF-FW01'], ['Router2', 'EB2-MDF-FW02'],
  ['Multilayer Switch1', 'EB2-MDF-CS'], ['Multilayer Switch0', 'EB1-F1-CS'],
  ['Multilayer Switch4', 'EB2-F2-DS01'], ['Multilayer Switch2', 'EB1-F2-DS01'], ['Multilayer Switch3', 'EB1-F3-DS01'],
  ['Switch4', 'EB2-F1-AS'], ['Switch5', 'EB2-F2-AS'], ['Switch6', 'EB2-F3-AS'],
  ['Switch1', 'EB1-F1-AS'], ['Switch2', 'EB1-F2-AS'], ['Switch3', 'EB1-F3-AS'],
  ['Wireless LAN Controller0', 'EB2-MDF-WLC01'], ['Light Weight Access Point0', 'EB2-F1-AP01'],
  ['PC0', 'EB2-STAFF-PC'], ['PC1', 'EB2-STUDENT-PC'], ['PC2', 'EB2-GUEST-PC'], ['PC3', 'EB1-STAFF-PC'],
  ['PC4', 'ADMIN-PC'], ['Server0', 'NVR'],
  ['PC5', 'EB2-F1-CAM01'], ['PC6', 'EB2-F1-PRN01'], ['PC7', 'EB1-F3-CAM01'], ['PC8', 'EB1-F3-PRN01'],
  ['Laptop0', 'EB2-STUDENT-LAPTOP']
];
for (var i = 0; i < NAMES.length; i++) {
  var d = n.getDevice(NAMES[i][0]);
  if (d) { d.setName(NAMES[i][1]); log.push('NAME ' + NAMES[i][0] + ' -> ' + NAMES[i][1]); }
  else { log.push('MISSING ' + NAMES[i][0]); }
}

dprint(log.join('\n'));
