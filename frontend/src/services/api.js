import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealthStatus = async () => {
  const response = await api.get('/health');
  return response.data;
};

// Surplus API
export const getSurplusListings = async () => {
  const response = await api.get('/surplus');
  return response.data;
};

export const getSurplusListingById = async (id) => {
  const response = await api.get(`/surplus/${id}`);
  return response.data;
};

export const parseSurplusText = async (rawText) => {
  const response = await api.post('/surplus/parse', { raw_text: rawText });
  return response.data;
};

export const createSurplusListing = async (data) => {
  const response = await api.post('/surplus/', data);
  return response.data;
};

// Demand API
export const getDemandListings = async () => {
  const response = await api.get('/demand');
  return response.data;
};

export const getDemandListingById = async (id) => {
  const response = await api.get(`/demand/${id}`);
  return response.data;
};

export const parseDemandText = async (rawText) => {
  const response = await api.post('/demand/parse', { raw_text: rawText });
  return response.data;
};

export const createDemandListing = async (data) => {
  const response = await api.post('/demand/', data);
  return response.data;
};

export const getOrganizations = async () => {
  const response = await api.get('/organizations');
  return response.data;
};

// Matching API (Phase 3.3)
export const matchSurplusAgainstDemands = async (surplusId, includeDisqualified = false) => {
  const response = await api.get(`/matching/surplus/${surplusId}`, {
    params: { include_disqualified: includeDisqualified },
  });
  return response.data;
};

export const matchDemandAgainstSurplus = async (demandId, includeDisqualified = false) => {
  const response = await api.get(`/matching/demand/${demandId}`, {
    params: { include_disqualified: includeDisqualified },
  });
  return response.data;
};

export const getTopMatchesForSurplus = async (surplusId, limit = 5) => {
  const response = await api.get(`/matching/surplus/${surplusId}/top`, {
    params: { limit },
  });
  return response.data;
};

export const explainMatch = async (surplusId, demandId) => {
  const response = await api.get(`/matching/explain/${surplusId}/${demandId}`);
  return response.data;
};

// Optimization API (Phase 4.2 & 4.3)
export const runOptimization = async () => {
  const response = await api.post('/optimization/run');
  return response.data;
};

export const getOptimizationSummary = async () => {
  const response = await api.get('/optimization/summary');
  return response.data;
};

// Impact Intelligence API (Phase 5)
export const getImpactSummary = async () => {
  const response = await api.get('/impact/summary');
  return response.data;
};

export const getImpactAllocations = async () => {
  const response = await api.get('/impact/allocations');
  return response.data;
};

export const getImpactTrends = async (groupBy = 'day') => {
  const response = await api.get('/impact/trends', {
    params: { group_by: groupBy },
  });
  return response.data;
};

export const getImpactCategories = async () => {
  const response = await api.get('/impact/categories');
  return response.data;
};

export const getImpactProviders = async () => {
  const response = await api.get('/impact/providers');
  return response.data;
};

export const getImpactPartners = async () => {
  const response = await api.get('/impact/partners');
  return response.data;
};

export const calculateImpact = async (allocations) => {
  const response = await api.post('/impact/calculate', { allocations });
  return response.data;
};

// Prediction API (Phase 3.2)
export const getPredictionMetrics = async () => {
  const response = await api.get('/predictions/metrics');
  return response.data;
};

export const getSurplusForecast = async (organizationId = 'hist-sup-001', category = 'Cooked Meals', startDate = new Date().toISOString().split('T')[0], days = 7) => {
  const response = await api.post('/predictions/surplus/forecast', {
    organization_id: organizationId,
    category,
    start_date: startDate,
    days,
  });
  return response.data;
};

export const getDemandForecast = async (organizationId = 'hist-rec-001', category = 'Cooked Meals', startDate = new Date().toISOString().split('T')[0], days = 7) => {
  const response = await api.post('/predictions/demand/forecast', {
    organization_id: organizationId,
    category,
    start_date: startDate,
    days,
  });
  return response.data;
};

export const predictSurplus = async (organizationId, category, targetDate, isEventDay = false) => {
  const response = await api.post('/predictions/surplus', {
    organization_id: organizationId,
    category,
    target_date: targetDate,
    is_event_day: isEventDay,
  });
  return response.data;
};

export const predictDemand = async (organizationId, category, targetDate, isEventDay = false) => {
  const response = await api.post('/predictions/demand', {
    organization_id: organizationId,
    category,
    target_date: targetDate,
    is_event_day: isEventDay,
  });
  return response.data;
};

export const retrainPredictionModels = async () => {
  const response = await api.post('/predictions/retrain');
  return response.data;
};


