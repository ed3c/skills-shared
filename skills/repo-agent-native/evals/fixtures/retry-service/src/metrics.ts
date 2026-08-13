export async function recordRetryFailure(
  operation: string,
  attempts: number,
): Promise<void> {
  if (!operation || attempts < 1) {
    throw new Error("invalid retry metric");
  }
}
