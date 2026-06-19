export function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

export function formatLabel(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function hasMeaningfulValue(value: unknown) {
  return value !== null && value !== undefined && value !== "" && !(Array.isArray(value) && value.length === 0);
}

export function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function formatDateTime(value?: string | null) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatMoney(value?: number | null) {
  if (value === null || value === undefined) {
    return "—";
  }

  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function shortId(value?: string | null, visible = 8) {
  if (!value) {
    return "—";
  }

  return value.length <= visible * 2 ? value : `${value.slice(0, visible)}...${value.slice(-visible)}`;
}

export function truncate(value?: string | null, limit = 140) {
  if (!value) {
    return "—";
  }

  const normalized = value.split(/\s+/).join(" ");
  if (normalized.length <= limit) {
    return normalized;
  }

  return `${normalized.slice(0, limit - 1).trim()}...`;
}
