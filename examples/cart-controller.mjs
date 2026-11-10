// A small, platform-neutral model of the native-cart interaction contract.
// The actual Shopify and Zoho adapters are not part of this portfolio example.
export class CartController {
  constructor(adapter) { this.adapter = adapter; this.pending = false; this.message = ''; }
  async add(variantId, quantity) {
    if (this.pending) return { status: 'ignored', reason: 'pending' };
    if (!variantId || !Number.isSafeInteger(quantity) || quantity < 1) {
      this.message = 'Select a variant and a whole quantity of at least one.';
      return { status: 'invalid' };
    }
    this.pending = true;
    this.message = 'Adding…';
    try {
      const receipt = await this.adapter.add({ variantId, quantity });
      if (!receipt?.ok) throw new Error('Cart did not confirm the request');
      this.message = 'Added to cart.';
      return { status: 'added', receipt };
    } catch {
      this.message = 'Unable to add. Please try again.';
      return { status: 'failed' };
    } finally {
      this.pending = false;
    }
  }
}
