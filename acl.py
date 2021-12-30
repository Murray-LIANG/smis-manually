import pywbemReq

import urllib3

urllib3.disable_warnings()


def show(subject, content=''):
    print('*' * 30)
    print(subject)
    print('-' * 30)
    print(content)
    print('*' * 30)
    print('')


def list_privilege(c, share):
    show('Listing Privileges')
    for p in c.References(share.path,
                          ResultClass='EMC_VNXe_CIFSShare_Identity'
                                      '_AssociatedPrivilegeAssocLeaf'):
        show('Existing Privileges', p.tomof())


def get_identity(c, user_name, create_if_not_found=True, top_cs=None,
                 acl_service=None):
    full_name = 'win2012.dev\\' + user_name
    users = [e for e in c.EnumerateInstances('EMC_VNXe_UserContactLeaf')
             if e['Name'] == full_name]

    if users:
        identity = conn.Associators(users[0].path,
                                    ResultClass='EMC_VNXe_IdentityLeaf')[0]
        show('Got Identity', identity.tomof())
        return identity

    if not users and create_if_not_found:
        contact = pywbemReq.CIMInstance(
            'CIM_UserContact',
            {'Name': full_name, 'CreationClassName': 'CIM_UserContact'})
        show('Creating Identity of User', contact.tomof())

        if not top_cs:
            top_cs = c.EnumerateInstances('EMC_VNXe_StorageSystemLeaf')[0]
        if not acl_service:
            acl_service = c.EnumerateInstances(
                'CIM_AccountManagementService')[0]

        result = c.InvokeMethod('CreateUserContact', acl_service.path,
                                System=top_cs.path,
                                UserContactTemplate=contact)
        show('Result of CreateUserContact', result[0])
        identity = c.GetInstance(result[1]['Identities'][0])
        show('Created Identity', identity.tomof())
        return identity

    show('User not found, and not to create', full_name)
    return None


def _assign_privilege(c, share, identities, privilege, share_service=None):
    if not share_service:
        cifs_server = c.EnumerateInstances('EMC_VNXe_CIFSServerLeaf')[0]
        share_service = c.Associators(cifs_server.path,
                                      ResultClass='CIM_FileExportService')[0]
    result = c.InvokeMethod("AssignPrivilegeToExportedShare",
                            share_service.path,
                            Identities=identities,
                            Activities=privilege,
                            FileShare=share.path)
    show('Result of AssignPrivilege', result[0])


def assign_read(c, share, identity_paths, share_service=None):
    _assign_privilege(c, share, identity_paths, [pywbemReq.Uint16(5)],
                      share_service)


def assign_write(c, share, identity_paths, share_service=None):
    _assign_privilege(c, share, identity_paths, [pywbemReq.Uint16(6)],
                      share_service)


def assign_full(c, share, identity_paths, share_service=None):
    _assign_privilege(c, share, identity_paths, [pywbemReq.Uint16(14)],
                      share_service)


if __name__ == '__main__':
    conn = pywbemReq.WBEMConnection('https://10.109.21.136:5989',
                                    ('Local/admin', 'Password123!'),
                                    default_namespace='root/emc/smis')

    cifs_share = [share for share in
                  conn.EnumerateInstances('EMC_VNXe_CIFSShareLeaf')
                  if share['InstanceID'] == 'SMBShare_6'][0]
    show('CIFS Share', cifs_share.tomof())

    list_privilege(conn, cifs_share)

    sids = ['S-1-5-15-f3286591-baeb1c6c-e75ba4e3-1f4',
            'S-1-5-15-f3286591-baeb1c6c-e75ba4e3-477',
            'S-1-5-15-f3286591-baeb1c6c-e75ba4e3-47a',
            'S-1-5-15-f3286591-baeb1c6c-e75ba4e3-47b']
    identities = [identity for identity
                  in conn.EnumerateInstances('EMC_VNXe_IdentityLeaf')
                  if identity['InstanceID'] in sids]
    users = [conn.Associators(identity.path,
                              ResultClass='EMC_VNXe_UserContactLeaf')[0]
             for identity in identities]
    for user, identity in zip(users, identities):
        show('User - Identity mapping', user.tomof() + identity.tomof())
    # top_cs = conn.EnumerateInstances('EMC_VNXe_StorageSystemLeaf')[0]
    # acl_service = conn.EnumerateInstances('CIM_AccountManagementService')[0]
    #
    # cifs_server = conn.EnumerateInstances('EMC_VNXe_CIFSServerLeaf')[0]
    # share_service = conn.Associators(cifs_server.path,
    #                                  ResultClass='CIM_FileExportService')[0]
    #
    # identity = get_identity(conn, 'SMIS_User_1', top_cs=top_cs,
    #                         acl_service=acl_service)

    # assign_full(conn, cifs_share, [identity.path, identity.path],
    #             share_service=share_service)
