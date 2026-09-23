const TEN = 10n;

function powerOfTen(scale) {
  return TEN ** BigInt(scale);
}

function parseParts(value) {
  const text = String(value ?? '').trim();
  if (!/^[-+]?\d+(?:\.\d+)?$/.test(text)) throw new Error(`Invalid decimal value: ${value}`);
  const negative = text.startsWith('-');
  const unsigned = text.replace(/^[-+]/, '');
  const [whole, fraction = ''] = unsigned.split('.');
  return { integer: BigInt(`${whole}${fraction}`), scale: fraction.length, negative };
}

function roundedDivision(numerator, denominator) {
  if (denominator <= 0n) throw new Error('Decimal divisor must be positive.');
  const sign = numerator < 0n ? -1n : 1n;
  const absolute = numerator < 0n ? -numerator : numerator;
  const quotient = absolute / denominator;
  const remainder = absolute % denominator;
  const rounded = remainder * 2n >= denominator ? quotient + 1n : quotient;
  return rounded * sign;
}

export function toScaledInteger(value, scale) {
  const parsed = parseParts(value);
  if (parsed.scale > scale) throw new Error(`Decimal value has more than ${scale} decimal places.`);
  const scaled = parsed.integer * powerOfTen(scale - parsed.scale);
  return parsed.negative ? -scaled : scaled;
}

export function multiplyToScale(left, right, scale) {
  const a = parseParts(left);
  const b = parseParts(right);
  const numerator = (a.negative ? -a.integer : a.integer) * (b.negative ? -b.integer : b.integer) * powerOfTen(scale);
  return roundedDivision(numerator, powerOfTen(a.scale + b.scale));
}

export function formatScaled(value, scale) {
  const integer = typeof value === 'bigint' ? value : BigInt(value);
  const negative = integer < 0n;
  const absolute = negative ? -integer : integer;
  const divisor = powerOfTen(scale);
  const whole = absolute / divisor;
  const fraction = String(absolute % divisor).padStart(scale, '0');
  return `${negative ? '-' : ''}${whole}${scale ? `.${fraction}` : ''}`;
}

export function compareScaled(left, right) {
  if (left < right) return -1;
  if (left > right) return 1;
  return 0;
}

export function roundHalfUp(numerator, denominator) {
  return roundedDivision(BigInt(numerator), BigInt(denominator));
}
