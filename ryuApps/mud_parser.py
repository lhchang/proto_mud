import pprint as pp
import socket

'''
This program generates a MUD object that is used to generate rules to push to respective switches
    
Composed of two parts:
    1. mud_model - metadata that describes the MUD file
    2. acl_model - the actual description of the flows
'''

class Mud(object):
    def __init__(self, mudFile):
        self.mudFile = mudFile
        self.mud_model = self.mudFile['ietf-mud:mud']
        self.acl_model = self.mudFile['ietf-access-control-list:access-lists']

        self.from_device_policy_name = None
        self.to_device_policy_name = None

        try:
            # [from-device-policy][access-lists][access-list] and [to-device-policy][access-lists][access-list]
            # are lists of names, experiments shown these have been only of size 1
            self.from_device_policy_name = self.mud_model['from-device-policy']['access-lists']['access-list'][0]['name'] # Name of the MUD's from-device-policy
            self.to_device_policy_name = self.mud_model['to-device-policy']['access-lists']['access-list'][0]['name'] # Name of the MUD's to-device-policy
        except TypeError as e:
            print 'Access Error: %s', e

        self.toFlows = {}
        self.fromFlows = {}

        self.__resolveACLs(self.to_device_policy_name, self.toFlows, dir='to-device') # lists in form of (dns_dst, protocol, srcport, dstport)
        self.__resolveACLs(self.from_device_policy_name, self.fromFlows,dir='from-device')  # lists in form of (dns_dst, protocol, srcport, dstport)

        self.__resolveDNS() # change to and from flows dns name to IP address


    #def __getFromDeviceFlowIds(self):
    #    '''
    #    Goes through list 'access-list' of dictionary 'from-device-policy' to get names of ACL
    #    :return: list of ACL names for flows going from the device
    #    '''
    #    from_aclNames = []
    #    from_acl = self.mud_model['from-device-policy']['access-lists']['access-list']
    #    for name_entry in from_acl:
    #        for key in name_entry:
    #            from_aclNames.append(name_entry[key])
    #    return from_aclNames


    #def __getToDeviceFlowIds(self):
    #    '''
    #
    #    :return: List of ACL names for flows going towards device
    #    '''
    #    to_aclNames = []
    #    to_acl = self.mud_model['to-device-policy']['access-lists']['access-list']
    #    for name_entry in to_acl:
    #        for key in name_entry:
    #            to_aclNames.append(name_entry[key])
    #    return to_aclNames


    def __resolveACLs(self, aclName, dirFlows, dir='to-device'):
        acl = self.acl_model['acl'] # list of access controls
        dns_dir = 'ietf-acldns:src-dnsname' # default value is src-dnsname

        if dir == 'from-device':  # if the direction is 'from-device' change the direction of traffic
            dns_dir = 'ietf-acldns:dst-dnsname'

        for acl_entry in acl:
            if acl_entry['name'] != aclName:
                continue
            if 'v4' in aclName: # check for which ip version. For simplicity of project we only consider ipv4
                ip_proto = 'ipv4'
            else:
                ip_proto = 'ipv6'
            ace = acl_entry['aces']['ace'] # ['aces']['ace'] is a list of dictionaries of matches to resolve

            # We assume only ipv4 addresses used
            for entry in ace:
                ace_name = entry['name']
                dns_name = entry['matches'][ip_proto][dns_dir]
                try: # if no protocol stated then it is considered 'any'
                    protocol = entry['matches'][ip_proto]['protocol']
                except KeyError as e:
                    print 'No key \'Protocol\': %s', e
                    print 'Any protocol is allowed'
                    protocol = None

                if protocol == 6: #TCP
                    if 'source-port' in entry['matches']['tcp']:
                        src_port = entry['matches']['tcp']['source-port']['port']
                    else:
                        src_port = '*'
                    if 'destination-port' in entry['matches']['tcp']:
                        dst_port = entry['matches']['tcp']['destination-port']['port']
                    else:
                        dst_port = '*'
                    dirFlows[ace_name] = [dns_name, protocol, src_port,dst_port]
                elif protocol == 17: #UDP
                    if 'source-port' in entry['matches']['udp']:
                        src_port = entry['matches']['udp']['source-port']['port']
                    else:
                        src_port = '*'
                    if 'destination-port' in entry['matches']['udp']:
                        dst_port = entry['matches']['udp']['destination-port']['port']
                    else:
                        dst_port = '*'
                    dirFlows[ace_name] = [dns_name, protocol, src_port, dst_port]
                else: # no indication of ports means 'any'
                    src_port = '*'
                    dst_port = '*'
                    dirFlows[ace_name] = [dns_name, protocol, src_port, dst_port]


    def __resolveDNS(self):
        try:
            for flow in self.toFlows:
                hostname = self.toFlows[flow][0]
                self.toFlows[flow][0] = socket.gethostbyname(hostname)
            for flow in self.fromFlows:
                hostname = self.fromFlows[flow][0]
                self.fromFlows[flow][0] = socket.gethostbyname(hostname)
        except socket.gaierror as e:
            print 'Error in __resolveDNS: %s' % e


