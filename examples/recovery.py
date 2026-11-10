"""Executable recovery pattern; synthetic adapter, no external service calls."""
from dataclasses import dataclass

@dataclass
class Store:
    product_id: str | None = None
    media_id: str | None = None
    linked: bool = False
    published: bool = False
    inventory: int = 0
    creates: int = 0
    uploads: int = 0

    def read(self):
        return dict(product_id=self.product_id, media_id=self.media_id,
                    linked=self.linked, published=self.published)

    def create(self):
        self.creates += 1
        self.product_id = 'demo-product-04'

    def upload(self):
        self.uploads += 1
        self.media_id = 'demo-media-04'

def resume(store, *, publication_approved=False, interrupt_after_upload=False):
    """Read the live state before retry; separately gate publication."""
    state = store.read()
    if not state['product_id']:
        store.create()
    if not state['media_id']:
        store.upload()
    if interrupt_after_upload:
        raise ConnectionError('Response lost after upload')
    # Read again: a response failure does not mean the write failed.
    state = store.read()
    if not state['linked']:
        store.linked = True
    if publication_approved:
        store.published = True
    return store.read()

if __name__ == '__main__':
    import json
    store = Store()
    try:
        resume(store, interrupt_after_upload=True)
    except ConnectionError:
        pass
    print(json.dumps({'after_interruption': store.read()}, indent=2))
    resume(store, publication_approved=True)
    print(json.dumps({'after_recovery': store.read(), 'creates': store.creates,
                      'uploads': store.uploads, 'inventory': store.inventory}, indent=2))
