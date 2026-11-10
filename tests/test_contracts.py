import unittest
from copy import deepcopy
from examples.recovery import Store,resume
from examples.verified_sync import SyncStore,apply_bundle

class RecoveryTests(unittest.TestCase):
    def test_lost_response_does_not_duplicate(self):
        s=Store()
        with self.assertRaises(ConnectionError): resume(s,interrupt_after_upload=True)
        resume(s,publication_approved=True)
        resume(s,publication_approved=True)
        self.assertEqual((s.creates,s.uploads),(1,1))
        self.assertTrue(s.linked and s.published)
        self.assertEqual(s.inventory,0)

    def test_preparation_does_not_publish(self):
        s=Store(); resume(s)
        self.assertFalse(s.published)
        self.assertEqual(s.inventory,0)

class SyncTests(unittest.TestCase):
    def setUp(self):
        self.store=SyncStore()
        self.initial=self.store.collect([[{'id':'A','units':2},{'id':'B','units':5}]],2)
        self.local,self.version=apply_bundle({},0,self.initial)

    def test_only_changed_record_transferred(self):
        b=self.store.collect([[{'id':'A','units':2},{'id':'B','units':7}]],2)
        self.assertEqual(list(b['changed']),['B'])
        updated,v=apply_bundle(self.local,self.version,b)
        self.assertEqual(updated['B']['units'],7); self.assertEqual(v,2)

    def test_partial_batch_preserves_cloud_revision(self):
        before=deepcopy(self.store.records)
        with self.assertRaises(ValueError): self.store.collect([[{'id':'A','units':9}]],2)
        self.assertEqual(self.store.records,before); self.assertEqual(self.store.revision,1)

    def test_tampering_preserves_local_data(self):
        b=self.store.collect([[{'id':'A','units':2},{'id':'B','units':7}]],2)
        b['changed']['B']['units']=999
        with self.assertRaises(ValueError): apply_bundle(self.local,self.version,b)
        self.assertEqual(self.local['B']['units'],5)

    def test_revision_gap_rejected(self):
        with self.assertRaises(ValueError): apply_bundle(self.local,9,self.initial)

    def test_deletion_is_explicit(self):
        b=self.store.collect([[{'id':'A','units':2}]],1)
        self.assertEqual(b['deleted'],['B'])
        updated,_=apply_bundle(self.local,self.version,b)
        self.assertNotIn('B',updated)

    def test_duplicate_source_id_rejected(self):
        with self.assertRaises(ValueError): self.store.collect([[{'id':'A'},{'id':'A'}]],2)

if __name__=='__main__': unittest.main()
