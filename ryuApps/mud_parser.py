import pprint as pp

class MudParser(object):
    def __init__(self, mudFile):
        self.mudFile = mudFile
        self.mud_model = self.mudFile['ietf-mud:mud']
        self.acl_model = self.mudFile['ietf-access-control-list:access-lists']
        self.toFlows = {}
        self.fromFlows = {}

        toDeviceACLNames = self.__getToDeviceFlowIds()
        fromDeviceACLNames = self.__getFromDeviceFlowIds()
        self.__resolveACLs(toDeviceACLNames, self.toFlows, dir='to-device') # tuples in form of (dns_dst, srcport, dstport)
        self.__resolveACLs(fromDeviceACLNames, self.fromFlows,dir='from-device')  # tuples in form of (dns_dst, srcport, dstport)

    def __getFromDeviceFlowIds(self):
        # Get name of the dictionanry we need to look for (list of dictionarys)
        from_aclNames = []
        from_acl = self.mud_model['from-device-policy']['access-lists']['access-list']
        for name_entry in from_acl:
            for key in name_entry:
                from_aclNames.append(name_entry[key])
        return from_aclNames

    def __getToDeviceFlowIds(self):
        to_aclNames = []
        to_acl = self.mud_model['to-device-policy']['access-lists']['access-list']
        for name_entry in to_acl:
            for key in name_entry:
                to_aclNames.append(name_entry[key])
        return to_aclNames

    def __resolveACLs(self, aclNames, dirFlows, dir='to-device'):
        acls = self.acl_model['acl'] # list of acls
        # names defining to/from policies
        dns_dir = 'ietf-acldns:src-dnsname'
        for name in aclNames:
            for acl_entry in acls:
                if acl_entry['name'] == name:
                    if 'v4' in name:
                        ip_proto = 'ipv4'
                    else:
                        ip_proto = 'ipv6'
                    if dir == 'from-device':
                        dns_dir = 'ietf-acldns:dst-dnsname'
                    ace = acl_entry['aces']['ace']
                    # We assume only ipv4 addresses used
                    for entry in ace:
                        ace_name = entry['name']
                        dns_name = entry['matches'][ip_proto][dns_dir]
                        protocol = entry['matches'][ip_proto]['protocol']
                        if protocol == 6: #TCP
                            src_port = entry['matches']['tcp']['source-port']['port']
                            dst_port = entry['matches']['tcp']['destination-port']['port']
                            dirFlows[ace_name] = (dns_name,src_port,dst_port)
                        elif protocol == 17: #UDP
                            src_port = entry['matches']['udp']['source-port']['port']
                            dst_port = entry['matches']['udp']['destination-port']['port']
                            dirFlows[ace_name] = (dns_name, src_port, dst_port)





























