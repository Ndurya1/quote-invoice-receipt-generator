import test from 'node:test';
import assert from 'node:assert/strict';
import { emitSessionExpired, subscribeSessionExpired } from '../src/auth/sessionEvents.js';

test('notifies and unsubscribes session-expired listeners', () => {
  const received = [];
  const unsubscribe = subscribeSessionExpired((error) => received.push(error));
  const error = new Error('expired');
  emitSessionExpired(error);
  unsubscribe();
  emitSessionExpired(new Error('ignored'));
  assert.deepEqual(received, [error]);
});
