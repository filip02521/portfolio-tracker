import { portfolioService } from '../portfolioService';

describe('PortfolioService', () => {
  describe('Cache Management', () => {
    it('should export portfolioService', () => {
      expect(portfolioService).toBeDefined();
      expect(typeof portfolioService.getSummary).toBe('function');
      expect(typeof portfolioService.getAssets).toBe('function');
      expect(typeof portfolioService.getTransactions).toBe('function');
    });

    it('should have proper method signatures', () => {
      expect(portfolioService.getSummary).toBeDefined();
      expect(portfolioService.getAssets).toBeDefined();
      expect(portfolioService.createTransaction).toBeDefined();
      expect(portfolioService.updateTransaction).toBeDefined();
      expect(portfolioService.deleteTransaction).toBeDefined();
    });
  });
});

