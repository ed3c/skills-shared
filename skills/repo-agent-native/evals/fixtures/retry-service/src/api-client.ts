import { retryRequest, type RetryResult } from "./retry-policy";
import { recordRetryFailure } from "./metrics";

export interface HttpTransport {
  get(path: string): Promise<string>;
}

export async function loadAccount(
  transport: HttpTransport,
  accountId: string,
  sleep: (milliseconds: number) => Promise<void>,
): Promise<RetryResult<string>> {
  const result = await retryRequest(
    () => transport.get(`/accounts/${accountId}`),
    sleep,
  );

  if (!result.ok) {
    try {
      await recordRetryFailure("loadAccount", result.attempts);
    } catch {
      // Metrics are best-effort and must not replace the domain result.
    }
  }

  return result;
}
