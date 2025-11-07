public class RetryUtil {
    private int maxRetries;

    public RetryUtil(int maxRetries) {
        this.maxRetries = maxRetries;
    }

    public void executeWithRetry(Runnable operation) throws Exception {
        for (int i = 0; i < maxRetries; i++) {
            try {
                operation.run();
                return;
            } catch (Exception e) {
                if (i == maxRetries - 1) {
                    throw e;
                }
            }
        }
    }
}
