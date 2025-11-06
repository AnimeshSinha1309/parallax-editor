function retryFetch(url, maxAttempts = 3) {
    for (let i = 0; i < maxAttempts; i++) {
        try {
            return fetch(url);
        } catch (error) {
            if (i === maxAttempts - 1) throw error;
        }
    }
}

class RetryManager {
    constructor(maxRetries = 5) {
        this.maxRetries = maxRetries;
    }

    async executeWithRetry(operation) {
        for (let attempt = 0; attempt < this.maxRetries; attempt++) {
            try {
                return await operation();
            } catch (error) {
                if (attempt === this.maxRetries - 1) throw error;
                console.log(`Retry attempt ${attempt + 1} failed`);
            }
        }
    }
}
