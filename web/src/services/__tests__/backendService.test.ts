import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BackendService } from '../backendService';
import { CardType } from '../../types/models';

describe('BackendService', () => {
  let service: BackendService;

  beforeEach(() => {
    service = new BackendService('http://localhost:8000');
    // Reset fetch mock
    global.fetch = vi.fn();
  });

  describe('fulfill', () => {
    it('should make POST request to /fulfill endpoint', async () => {
      const mockResponse = {
        cards: [
          {
            header: 'Test',
            text: 'Test completion',
            type: CardType.COMPLETION,
          },
        ],
        processing: true,
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const request = {
        user_id: 'test-user',
        document_text: 'Hello world',
        cursor_position: [0, 11] as [number, number],
        global_context: {
          scope_root: '/test',
        },
      };

      const result = await service.fulfill(request);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/fulfill',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request),
        })
      );

      expect(result).toEqual(mockResponse);
      expect(result.processing).toBe(true);
    });

    it('should throw error on failed request', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      const request = {
        user_id: 'test-user',
        document_text: 'Hello',
        cursor_position: [0, 5] as [number, number],
        global_context: {
          scope_root: '/test',
        },
      };

      await expect(service.fulfill(request)).rejects.toThrow('Fulfill request failed: 500');
    });
  });

  describe('getCached', () => {
    it('should make GET request to /cached/{id} endpoint', async () => {
      const mockResponse = {
        cards: [
          {
            header: 'Cached',
            text: 'Cached content',
            type: CardType.CONTEXT,
          },
        ],
        processing: false,
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await service.getCached('test-user');

      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/cached/test-user');
      expect(result).toEqual(mockResponse);
      expect(result.processing).toBe(false);
    });

    it('should throw error on failed request', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      });

      await expect(service.getCached('test-user')).rejects.toThrow('Get cached failed: 404');
    });
  });

  describe('clearFeed', () => {
    it('should make DELETE request to /user/{id}/feed endpoint', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
      });

      await service.clearFeed('test-user');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/user/test-user/feed',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });

  describe('health', () => {
    it('should make GET request to /health endpoint', async () => {
      const mockHealth = {
        status: 'healthy',
        fulfillers: {
          completions: true,
          ambiguities: true,
          web_context: true,
          code_search: true,
        },
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealth,
      });

      const result = await service.health();

      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/health');
      expect(result).toEqual(mockHealth);
    });
  });
});
