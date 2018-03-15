class MudParser(object):
    def __init__(self, mudFile):
        self.mudFile = mudFile
        self.mud_model = self.mudFile['ietf-mud:mud']
        self.acl_model = self.mudFile['ietf-access-control-list:access-lists']
        self.toFlows = {}
        self.fromFlows = {}

        to_aclNames = self.__getToFlowIds()
        from_aclNames = self.__getFromFlowIds()
        self.__resolveACLs(to_aclNames, self.toFlows) # tuples in form of (ace name, dns_dst, srcport, dstport)


    def __getFromFlowIds(self):
        # Get name of the dictionanry we need to look for (list of dictionarys)
        from_aclNames = []
        from_acl = self.mud_model['from-device-policy']['access-lists']['access-list']
        for name_entry in from_acl:
            for key in name_entry:
                from_aclNames.append(name_entry[key])
        return from_aclNames

    def __getToFlowIds(self):
        to_aclNames = []
        to_acl = self.mud_model['to-device-policy']['access-lists']['access-list']
        for name_entry in to_acl:
            for key in name_entry:
                to_aclNames.append(name_entry[key])
        return to_aclNames

    def __resolveACLs(self, aclNames, dirFlows):
        acls = self.acl_model['acl'] # list of acls
        # names defining to/from policies
        for name in aclNames:
            for acl_entry in acls:
                if acl_entry['name'] == name:
                    if 'v4' in name:
                        ip_proto = 'ipv4'
                    else:
                        ip_proto = 'ipv6'
                    ace = acl_entry['aces']['ace']
                    # We assume only ipv4 addresses used
                    for entry in ace:
                        ace_name = entry['name']
                        dns_name = entry['matches'][ip_proto]['ietf-acldns:src-dnsname']
                        protocol = entry['matches'][ip_proto]['protocol']
                        if protocol == 6: #TCP
                            src_port = entry['matches']['tcp']['source-port']['port']
                            dst_port = entry['matches']['tcp']['destination-port']['port']
                            dirFlows[name] = (name,dns_name,src_port,dst_port)
                        elif protocol == 17: #UDP
                            src_port = entry['matches']['udp']['source-port']['port']
                            dst_port = entry['matches']['udp']['destination-port']['port']
                            dirFlows[ace_name] = (name, dns_name, src_port, dst_port)






























