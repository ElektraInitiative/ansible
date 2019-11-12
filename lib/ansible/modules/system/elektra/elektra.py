#!/usr/bin/python


from ansible.module_utils.basic import AnsibleModule
import kdb
from collections import OrderedDict

class ElektraException(Exception):
    """ elektraException """
    pass

class ElektraMountException(ElektraException):
    """Mount failed"""
    pass
class ElektraUmountException(ElektraException):
    """Umount failed"""
    pass
class ElektraReadException(ElektraException):
    """Failed to read keyset"""
    pass
class ElektraWriteException(ElektraException):
    """Failed to write keyset"""
    pass

# Flattens keyset except for "meta" or "value" dicts
def flatten_json(y):
    out = OrderedDict()
    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                if str(a) == "value":
                    try:
                        type(out[name[:-1]])
                    except:
                        out[name[:-1]] = {}
                    out[name[:-1]]['value'] = x[a]
                elif str(a) == "meta":
                    try:
                        type(out[name[:-1]])
                    except:
                        out[name[:-1]] = {}
                    out[name[:-1]]['meta'] = x[a]
                else:
                    flatten(x[a], name + a + '/')
        else:
            out[name[:-1]] = x
    flatten(y)
    return out

def elektraSet(mountpoint, keyset, keeporder):
    with kdb.KDB() as db:
        ks = kdb.KeySet(0)
        rc = 0
        try:
            rc = db.get(ks, mountpoint)
        except kdb.KDBException as e:
            raise ElektraReadException("KDB.get failed: {}".format(e))
        if rc == -1:
            raise ElektraReadException("Failed to read keyset below {}".format(mountpoint))
        flattenedKeyset = flatten_json(keyset)
        i = 0
        for name, value in flattenedKeyset.items():
            key = None
            kname = None
            try:
                key = ks[mountpoint+"/"+name]
                if keeporder and key.hasMeta("order"):
                    i = int((key.getMeta("order").value))+1
                if keeporder:
                    key.setMeta("order", str(i))
                    i += 1
            except KeyError:
                key = kdb.Key(mountpoint+"/"+name)
                if keeporder:
                    key.setMeta("order", str(i))
                    i += 1
                ks.append(key)
            if isinstance(value, dict):
                for sname, svalue in value.items():
                    if sname == 'value':
                        key.value = svalue
                    elif sname == 'meta':
                        for mname, mvalue in svalue.items():
                            key.setMeta(mname, str(mvalue))
            else:
                key.value = value
        try:
            rc = db.set(ks, mountpoint)
        except kdb.KDBException as e:
            raise ElektraWriteException("KDB.set failed: {}".format(e))
        if rc == -1:
            raise ElektraWriteException("Failed to write keyset to {}".format(mountpoint))
        return rc

def elektraMount(mountpoint, filename, resolver, plugins, recommends):
    with kdb.KDB() as db:
        ks = kdb.KeySet(0)
        mountpoints = "system/elektra/mountpoints"
        rc = 0
        try:
            rc = db.get(ks, mountpoints)
        except kdb.KDBException as e:
            raise ElektraReadException("KDB.get failed: {}".format(e))
        if rc == -1:
            raise ElektraMountException("Failed to fetch elektra facts: failed to read system/elektra/mountpoints.")
        searchKey = mountpoints +'/'+ mountpoint.replace('/', '\/')
        try:
            key = ks[searchKey]
            return 0
        except KeyError:
            return 1

def elektraUmount(mountpoint):
    with kdb.KDB() as db:
        ks = kdb.KeySet(0)
        mountpoints = "system/elektra/mountpoints"
        rc = 0
        try:
            rc = db.get(ks, mountpoints)
        except kdb.KDBException as e:
            raise ElektraReadException("KDB.get failed: {}".format(e))
        if rc != 1:
            raise ElektraUmountException("Failed to fetch elektra facts: failed to read system/elektra/mountpoints.")
        key = kdb.Key()
        key.name = mountpoints+'/'+mountpoint.replace('/', '\/')
        ks.cut(key)
        try:
            rc = db.set(ks, mountpoints)
        except kdb.KDBException as e:
            raise ElektraWriteException("KDB.set failed: {}".format(e))
        if rc != 1:
            raise ElektraUmountException("Failed to umount "+key.name)

def main():
    module = AnsibleModule(
            argument_spec=dict(
                name=dict(type='str'),
                mountpoint=dict(type='str'),
                keys=dict(type='raw', default={}),
                recommends=dict(type='bool', default=True),         # mount with --with-recommends
                filename=dict(type='str', default=''),
                resolver=dict(type='str', default='resolver'),
                plugins=dict(type='list', elements='dict'),
                keeporder=dict(type='bool', default=False),         # if True: add "order" metakey for each "keys"-element based on the original argument order
                )
            )
    name = module.params.get('name')
    keys = module.params.get('keys')
    mountpoint = module.params.get('mountpoint')
    plugins = module.params.get('plugins')
    resolver = module.params.get('resolver')
    filename = module.params.get('filename')
    recommends = module.params.get('recommends')
    keeporder = module.params.get('keeporder')
    json_output={}                                                  
    json_output['changed'] = False

    mountpointExists = True     # Indicates if mountpoint already exists prior to calling the module. If not/"False" unmount it on failure
    rc = 0
    if plugins or filename != '':
        try:
            rc = elektraMount(mountpoint, filename, resolver, plugins, recommends)
            if rc == 1:
                mountpointExists = False
            json_output['mount rc'] = rc
        except ElektraMountExecption as e:
            module.fail_json(msg="Failed to mount configuration {} to {}: {}".format(filename, mountpoint, e))
    try:
        rc = elektraSet(mountpoint, keys, keeporder)
    except ElektraWriteException as e:
        json_output['ERROR']=e
        try:
            if not mountpointExists:
                elektraUmount(mountpoint)
        except ElektraUmountException as e:
            module.fail_json(msg="Failed to unmount {}: {}".format(mountpoint, e))
        module.fail_json(msg="Failed to write configuration to {}: {}".format(mountpoint, e))
    if rc == 1:
        json_output['changed'] = True
    module.exit_json(**json_output)      


if __name__ == '__main__':
    main()

