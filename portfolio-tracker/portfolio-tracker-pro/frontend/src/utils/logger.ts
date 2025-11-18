/**
 * Logger utility - conditionally logs based on environment
 * In production, logs are disabled to improve performance
 */

const isDevelopment = process.env.NODE_ENV === 'development';

interface Logger {
  log: (...args: unknown[]) => void;
  warn: (...args: unknown[]) => void;
  error: (...args: unknown[]) => void;
  info: (...args: unknown[]) => void;
  debug: (...args: unknown[]) => void;
}

export const logger: Logger = {
  log: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.log(...args);
    }
  },
  
  warn: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.warn(...args);
    }
  },
  
  error: (...args: unknown[]): void => {
    // Always log errors, even in production
    // But filter out "canceled" errors from AbortController (normal during hot reload)
    const firstArg = args[0];
    if (typeof firstArg === 'string' && (firstArg.includes('canceled') || firstArg.includes('Request setup error'))) {
      // Silently ignore canceled requests - they're normal during hot reload
      return;
    }
    console.error(...args);
  },
  
  info: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.info(...args);
    }
  },
  
  debug: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.debug(...args);
    }
  },
};

export default logger;
