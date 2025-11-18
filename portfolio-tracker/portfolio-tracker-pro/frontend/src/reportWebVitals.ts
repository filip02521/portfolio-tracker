import {
  getCLS,
  getFID,
  getFCP,
  getLCP,
  getTTFB,
  ReportHandler
} from 'web-vitals';

const reportWebVitals = (onPerfEntry?: ReportHandler) => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    getCLS(onPerfEntry);
    getFID(onPerfEntry);
    getFCP(onPerfEntry);
    getLCP(onPerfEntry);
    getTTFB(onPerfEntry);
  }
};

// Enhanced Web Vitals reporting with detailed logging
const logWebVitals = (metric: any) => {
  // Only log in development
  if (process.env.NODE_ENV === 'development') {
    console.log(`${metric.name}:`, metric.value, metric.rating);
  }
  
  // In production, send to analytics endpoint (TODO: implement)
  // if (process.env.NODE_ENV === 'production') {
  //   fetch('/api/analytics/web-vitals', {
  //     method: 'POST',
  //     body: JSON.stringify(metric),
  //     headers: { 'Content-Type': 'application/json' }
  //   }).catch(console.error);
  // }
};

reportWebVitals(logWebVitals);
export default reportWebVitals;
