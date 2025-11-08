/**
 * Backend API service for communicating with Parallizer
 */

import type { FulfillRequest, FulfillResponse } from '../types/models';
import { config } from '../utils/config';

export interface FulfillResponseWithStatus extends FulfillResponse {
  processing: boolean;
}

export class BackendService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  /**
   * POST /fulfill - Initial fulfillment request
   * Returns immediate response with cached cards + processing status
   */
  async fulfill(request: FulfillRequest): Promise<FulfillResponseWithStatus> {
    const response = await fetch(`${this.baseUrl}/fulfill`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Fulfill request failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  }

  /**
   * GET /user/{user_id}/cached - Poll for incremental updates
   * Returns current cached cards + processing status
   */
  async getCached(userId: string): Promise<FulfillResponseWithStatus> {
    const response = await fetch(`${this.baseUrl}/user/${userId}/cached`);

    if (!response.ok) {
      throw new Error(`Get cached failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  }

  /**
   * DELETE /user/{user_id}/feed - Clear user's feed
   */
  async clearFeed(userId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/user/${userId}/feed`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Clear feed failed: ${response.status} ${response.statusText}`);
    }
  }

  /**
   * GET /health - Check backend health
   */
  async health(): Promise<{ status: string; fulfillers: Record<string, boolean> }> {
    const response = await fetch(`${this.baseUrl}/health`);

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return response.json();
  }
}

// Singleton instance
export const backendService = new BackendService(config.backendUrl);
