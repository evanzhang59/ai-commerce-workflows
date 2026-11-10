"""Complete-batch publication and verified local replacement, using fake records."""
import hashlib,json
from copy import deepcopy

def canonical(records):
    return json.dumps(records, sort_keys=True, separators=(',', ':')).encode()

def digest(records):
    return hashlib.sha256(canonical(records)).hexdigest()

class SyncStore:
    def __init__(self):
        self.records = {}
        self.revision = 0

    def collect(self, pages, expected_count):
        candidate = {}
        for page in pages:
            for record in page:
                identity = record['id']
                if identity in candidate:
                    raise ValueError('Duplicate source identity')
                candidate[identity] = deepcopy(record)
        if len(candidate) != expected_count:
            raise ValueError('Incomplete batch; keep current revision')
        # Full source read; downstream storage and transfer can still be incremental.
        changed = {k:v for k,v in candidate.items() if self.records.get(k) != v}
        deleted = sorted(set(self.records)-set(candidate))
        bundle = dict(base=self.revision, revision=self.revision+1,
                      changed=changed, deleted=deleted, count=len(candidate),
                      sha256=digest(candidate))
        self.records, self.revision = candidate, self.revision+1
        return bundle

def apply_bundle(current, revision, bundle):
    if bundle['base'] != revision:
        raise ValueError('Revision gap; request a baseline')
    candidate = deepcopy(current)
    candidate.update(bundle['changed'])
    for identity in bundle['deleted']:
        candidate.pop(identity, None)
    if len(candidate) != bundle['count'] or digest(candidate) != bundle['sha256']:
        raise ValueError('Verification failed; do not replace local data')
    return candidate, bundle['revision']

if __name__ == '__main__':
    store = SyncStore()
    baseline = store.collect([[{'id':'A','units':2},{'id':'B','units':5}]], 2)
    local, version = apply_bundle({}, 0, baseline)
    delta = store.collect([[{'id':'A','units':2},{'id':'B','units':7}]], 2)
    local, version = apply_bundle(local, version, delta)
    print(json.dumps({'delta':delta, 'verified_local':local}, indent=2))
