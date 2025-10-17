#!/usr/bin/env node
const { performance } = require('perf_hooks');
const { blake2b } = require('blakejs');
const bs58 = require('bs58');

function generateDeterministicDid(commitment, network = 'mainnet') {
  let commitmentBytes;
  if (typeof commitment === 'string') {
    if (commitment.length === 64) {
      commitmentBytes = new Uint8Array(commitment.match(/.{2}/g).map(byte => parseInt(byte, 16)));
    } else {
      const buffer = Buffer.from(commitment, 'base64');
      commitmentBytes = new Uint8Array(buffer.buffer, buffer.byteOffset, buffer.length);
    }
  } else {
    commitmentBytes = commitment;
  }

  const hash = blake2b(commitmentBytes, undefined, 32);
  const base58Hash = bs58.encode(hash);
  return `did:cardano:${network}:${base58Hash}`;
}

function randomCommitment() {
  const arr = new Uint8Array(32);
  for (let i = 0; i < arr.length; i += 1) {
    arr[i] = Math.floor(Math.random() * 256);
  }
  return arr;
}

function recordTimings(label, iterations, fn) {
  const durations = [];
  for (let i = 0; i < iterations; i += 1) {
    const start = performance.now();
    fn();
    durations.push(performance.now() - start);
  }
  durations.sort((a, b) => a - b);
  const p50 = durations[Math.floor(durations.length * 0.5)];
  const p95 = durations[Math.floor(durations.length * 0.95)];
  const p99 = durations[Math.min(durations.length - 1, Math.floor(durations.length * 0.99))];
  const avg = durations.reduce((sum, val) => sum + val, 0) / durations.length;
  console.log(`\n${label}`);
  console.log(`Iterations: ${iterations}`);
  console.log(`Average: ${avg.toFixed(3)} ms`);
  console.log(`P50: ${p50.toFixed(3)} ms`);
  console.log(`P95: ${p95.toFixed(3)} ms`);
  console.log(`P99: ${p99.toFixed(3)} ms`);
}

function main() {
  const deterministicRuns = 50;
  const commitment = randomCommitment();
  const did = generateDeterministicDid(commitment);
  console.log('Sample DID:', did);
  recordTimings('Deterministic DID generation', deterministicRuns, () => {
    generateDeterministicDid(randomCommitment());
  });
  recordTimings('Deterministic DID regeneration (cached commitment)', deterministicRuns, () => {
    generateDeterministicDid(commitment);
  });
}

if (require.main === module) {
  main();
}
