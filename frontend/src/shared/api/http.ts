export function buildAuthHeaders(authorization?: string) {
  return {
    authorization: authorization ?? undefined,
  }
}
