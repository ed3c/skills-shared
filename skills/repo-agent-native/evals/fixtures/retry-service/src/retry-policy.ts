export type RetryResult<T> =
  | { ok: true; value: T; attempts: number }
  | { ok: false; error: Error; attempts: number };

export const MAX_ATTEMPTS = 3;
export const RETRY_DELAY_MS = 25;

export async function retryRequest<T>(
  operation: () => Promise<T>,
  sleep: (milliseconds: number) => Promise<void>,
): Promise<RetryResult<T>> {
  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
    try {
      return { ok: true, value: await operation(), attempts: attempt };
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      if (attempt < MAX_ATTEMPTS) {
        await sleep(RETRY_DELAY_MS);
      }
    }
  }

  return {
    ok: false,
    error: lastError ?? new Error("retry failed without an error"),
    attempts: MAX_ATTEMPTS,
  };
}
