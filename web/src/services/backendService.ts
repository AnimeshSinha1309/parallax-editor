/**
 * Backend API service for communicating with Parallizer
 */

import type { FulfillRequest, FulfillResponse, FileNode } from '../types/models';
import { config } from '../utils/config';

export interface FulfillResponseWithStatus extends FulfillResponse {
  processing: boolean;
}

export interface FileContentResponse {
  content: string;
  language: string;
  path: string;
}

export interface FileSaveResponse {
  status: string;
  message: string;
  bytes: number;
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

  /**
   * GET /files/tree - Get directory tree structure
   */
  async getFileTree(scopeRoot: string, maxDepth: number = 10): Promise<FileNode> {
    const params = new URLSearchParams({
      scope_root: scopeRoot,
      max_depth: maxDepth.toString(),
    });

    const response = await fetch(`${this.baseUrl}/files/tree?${params}`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to get file tree: ${response.status}`);
    }

    return response.json();
  }

  /**
   * POST /files/content - Read file content
   */
  async getFileContent(path: string, scopeRoot: string): Promise<FileContentResponse> {
    const response = await fetch(`${this.baseUrl}/files/content`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, scope_root: scopeRoot }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to read file: ${response.status}`);
    }

    return response.json();
  }

  /**
   * POST /files/save - Save file content
   */
  async saveFile(path: string, content: string, scopeRoot: string): Promise<FileSaveResponse> {
    const response = await fetch(`${this.baseUrl}/files/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, content, scope_root: scopeRoot }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to save file: ${response.status}`);
    }

    return response.json();
  }
}

// Singleton instance
export const backendService = new BackendService(config.backendUrl);
