import {test} from 'node:test';
import assert from 'node:assert/strict';
import {api} from './api.js';

test('POST obtains CSRF token and sends same-origin JSON', async () => {
  const calls = [];
  globalThis.fetch = async (path, options) => {
    calls.push([path, options]);
    return {ok: true, json: async () => path === '/api/session/' ? {csrf: 'csrf-test'} : {job_id: 'job-test'}};
  };
  assert.deepEqual(await api('jobs/submit/', {kind: 'inspect'}), {job_id: 'job-test'});
  assert.equal(calls[0][0], '/api/session/');
  assert.equal(calls[1][1].headers['X-CSRFToken'], 'csrf-test');
  assert.equal(calls[1][1].credentials, 'same-origin');
  assert.equal(calls[1][1].body, '{"kind":"inspect"}');
});

test('API failure gives actionable server message', async () => {
  globalThis.fetch = async () => ({ok: false, status: 400, json: async () => ({error: 'Choose a column.'})});
  await assert.rejects(api('jobs/submit/', {}), /Choose a column/);
});

test('non-JSON gateway errors are handled', async () => {
  globalThis.fetch = async () => ({ok: false, status: 502, json: async () => {throw new Error('HTML');}});
  await assert.rejects(api('jobs/'), /Request failed \(502\)/);
});
