import crypto from 'node:crypto';

// Each half-open address range belongs to exactly one switch. Start from stock,
// then copy enabled ranges from the assembled source, including its helpers.
export const features = {
  fixes: [[0xd629,0xd62b], [0xd7cf,0xd7e2], [0xdf53,0xdf71],
    [0xe188,0xe189], [0xe18b,0xe18c], [0xe47c,0xe4a0], [0xe4da,0xe500],
    [0xe65b,0xe672], [0xe800,0xe815], [0xebed,0xec00], [0xec18,0xec38],
    [0xeff5,0xeff6], [0xf0ed,0xf102], [0xf26f,0xf279], [0xf513,0xf514],
    [0xf822,0xf834], [0xfe5d,0xfe66]],
  rainbow: [[0xe426,0xe429], [0xe929,0xe975]],
  banner: [[0xe437,0xe44d]],
};
export const hash = data => crypto.createHash('sha256').update(data).digest('hex');
export const variantId = options => Object.keys(features)
  .map(key => `${key}-${options[key] ? 'on' : 'off'}`).join('_');

export function compose(original, assembled, options) {
  if (original.length !== 16384 || assembled.length !== 16384) {
    throw new Error('Both input images must be 16 KB');
  }
  const owners = new Map();
  for (const [feature, ranges] of Object.entries(features)) {
    if (typeof options[feature] !== 'boolean') throw new Error(`Invalid ${feature} option`);
    for (const [start, end] of ranges) {
      if (start < 0xc000 || end > 0x10000 || start >= end) throw new Error('Invalid patch range');
      for (let address = start; address < end; address++) {
        if (owners.has(address)) throw new Error(`Overlapping patch range at ${address}`);
        owners.set(address, feature);
      }
    }
  }
  const result = Buffer.from(original);
  for (let i = 0; i < assembled.length; i++) {
    const owner = owners.get(0xc000 + i);
    if (assembled[i] !== original[i] && !owner) {
      throw new Error(`Unclassified assembled change at $${(0xc000+i).toString(16)}`);
    }
    if (owner && options[owner]) result[i] = assembled[i];
  }
  return result;
}

export function allOptions() {
  return Array.from({length: 8}, (_, mask) => ({
    fixes: Boolean(mask & 1), rainbow: Boolean(mask & 2), banner: Boolean(mask & 4),
  }));
}
