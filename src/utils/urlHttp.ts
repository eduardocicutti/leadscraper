export function urlHttp(valor: unknown): string | undefined {
  if (typeof valor !== "string") return undefined;
  try {
    const url = new URL(valor);
    if (
      (url.protocol === "https:" || url.protocol === "http:") &&
      !url.username &&
      !url.password
    )
      return url.href;
  } catch {
    return undefined;
  }
  return undefined;
}
