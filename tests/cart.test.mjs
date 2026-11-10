import test from 'node:test';
import assert from 'node:assert/strict';
import { CartController } from '../examples/cart-controller.mjs';

test('passes the exact selected variant and quantity', async () => {
  let received;
  const c = new CartController({ add: async value => { received = value; return { ok: true }; } });
  assert.equal((await c.add('demo-200ml', 2)).status, 'added');
  assert.deepEqual(received, { variantId: 'demo-200ml', quantity: 2 });
});
test('duplicate clicks do not issue a second pending request', async () => {
  let resolve, calls = 0;
  const c = new CartController({ add: () => { calls++; return new Promise(r => { resolve = r; }); } });
  const first = c.add('demo-100ml', 1);
  assert.equal((await c.add('demo-100ml', 1)).status, 'ignored');
  resolve({ ok: true }); await first;
  assert.equal(calls, 1); assert.equal(c.pending, false);
});
test('invalid quantities never reach the adapter', async () => {
  const c = new CartController({ add: async () => { throw new Error('must not run'); } });
  for (const quantity of [0, -1, 1.5, NaN, Infinity]) assert.equal((await c.add('demo', quantity)).status, 'invalid');
  assert.equal((await c.add('', 1)).status, 'invalid');
});
test('failure resets the control and a later retry can succeed', async () => {
  let calls = 0;
  const c = new CartController({ add: async () => { if (++calls === 1) throw new Error('offline'); return { ok: true }; } });
  assert.equal((await c.add('demo', 1)).status, 'failed');
  assert.equal(c.pending, false);
  assert.equal((await c.add('demo', 1)).status, 'added');
});
